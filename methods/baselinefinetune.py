import backbone
import paddle
import paddle.nn as nn
import numpy as np
from methods.meta_template import MetaTemplate
import paddle.optimizer as optim


class BaselineFinetune(MetaTemplate):
    def __init__(self, model_func, n_way, n_support, loss_type="softmax"):
        super(BaselineFinetune, self).__init__(model_func, n_way, n_support)
        self.loss_type = loss_type

    def set_forward(self, x, is_feature=True):
        return self.set_forward_adaptation(x, is_feature)  # Baseline always do adaptation

    def set_forward_adaptation(self, x, is_feature=True):
        assert is_feature == True, 'Baseline only support testing with feature'
        z_support, z_query = self.parse_feature(x, is_feature)

        z_support = z_support.reshape([self.n_way * self.n_support, -1])
        z_query = z_query.reshape([self.n_way * self.n_query, -1])

        y_support = paddle.to_tensor(np.repeat(range(self.n_way), self.n_support))

        if self.loss_type == 'softmax':
            linear_clf = nn.Linear(self.feat_dim, self.n_way)
        elif self.loss_type == 'dist':
            linear_clf = backbone.distLinear(self.feat_dim, self.n_way)

        set_optimizer = optim.Momentum(learning_rate=0.01,
                                       momentum=0.9,
                                       parameters=linear_clf.parameters(),
                                       weight_decay=0.001)

        loss_function = nn.CrossEntropyLoss()

        batch_size = 4
        support_size = self.n_way * self.n_support
        for epoch in range(100):
            rand_id = np.random.permutation(support_size)
            for i in range(0, support_size, batch_size):
                set_optimizer.clear_grad()
                selected_id = paddle.to_tensor(rand_id[i: min(i + batch_size, support_size)]).cuda()
                z_batch = z_support[selected_id]
                y_batch = y_support[selected_id]
                scores = linear_clf(z_batch)
                loss = loss_function(scores, y_batch.cast('int64'))
                loss.backward()
                set_optimizer.step()
        scores = linear_clf(z_query)
        return scores

    def set_forward_loss(self, x):
        raise ValueError('Baseline predict on pretrained feature and do not support finetune backbone')