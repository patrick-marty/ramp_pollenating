import os
os.environ["THEANO_FLAGS"] = "device=gpu"
import theano
 
import numpy as np
from sklearn.base import BaseEstimator
from lasagne import layers, nonlinearities, updates, init, objectives
from lasagne.updates import nesterov_momentum
from nolearn.lasagne import NeuralNet, BatchIterator
from nolearn.lasagne.handlers import EarlyStopping

 
 
class FlipBatchIterator(BatchIterator):
    def transform(self, Xb, yb):
        Xb, yb = super(FlipBatchIterator, self).transform(Xb, yb)
        # Flip half of the images in this batch at random:
        bs = Xb.shape[0]
        indices = np.random.choice(bs, bs / 2, replace=False)
        Xb[indices] = Xb[indices, :, ::-1]
        
        # Drop randomly half of the features in each batch:
        bf = Xb.shape[2]
        indices_features = np.random.choice(bf, bf / 2, replace=False)
        Xb = Xb.transpose((2, 0, 1, 3))
        Xb[indices_features] = Xb[indices_features]
        Xb = Xb.transpose((1, 2, 0, 3))
        return Xb, yb
 
    
class Classifier(BaseEstimator):
 
    def __init__(self):
        self.net = build_model(hyper_parameters)
 
    def preprocess(self, X):
        X = (X / 255.)
        X = X.astype(np.float32)
        X = X[:, 10:54, 10:54, :]
        X = X.transpose((0, 3, 1, 2))
        return X
 
    def fit(self, X, y):
        X = self.preprocess(X)
        self.net.fit(X, y)
        return self
 
    def predict(self, X):
        X = self.preprocess(X)
        return self.net.predict(X)
 
    def predict_proba(self, X):
        X = self.preprocess(X)
        return self.net.predict_proba(X)
 
def build_model(hyper_parameters):
    net = NeuralNet(
        layers=[
            ('input', layers.InputLayer),
            ('conv1', layers.Conv2DLayer),
            ('pool1', layers.MaxPool2DLayer),
            ('conv2', layers.Conv2DLayer),
            ('pool2', layers.MaxPool2DLayer),
            ('conv3', layers.Conv2DLayer),
            ('pool3', layers.MaxPool2DLayer),
            ('hidden4', layers.DenseLayer),
            ('hidden5', layers.DenseLayer),
            ('hidden6', layers.DenseLayer),
            ('output', layers.DenseLayer),
            ],
        input_shape=(None, 3, 44, 44),
        use_label_encoder=True,
        verbose=1,
        **hyper_parameters
        )
    return net
 
hyper_parameters = dict(
    conv1_num_filters=128, conv1_filter_size=(2, 2), pool1_pool_size=(2, 2),
    conv2_num_filters=256, conv2_filter_size=(1, 1), pool2_pool_size=(2, 2),
    conv3_num_filters=128, conv3_filter_size=(2, 2), pool3_pool_size=(4, 4),
    hidden4_num_units=1024,
    hidden4_nonlinearity=nonlinearities.rectify,
    hidden4_W=init.GlorotUniform(gain='relu'),
    hidden5_num_units=512,
    hidden5_nonlinearity=nonlinearities.leaky_rectify,
    hidden5_W=init.GlorotUniform(gain='relu'),
    hidden6_num_units=256,
    hidden6_nonlinearity=nonlinearities.very_leaky_rectify,
    hidden6_W=init.GlorotUniform(gain='relu'),
    output_num_units=18,
    output_nonlinearity=nonlinearities.softmax,
    update_learning_rate=0.01,
    update=updates.adagrad,
    max_epochs=200,
    on_epoch_finished=[EarlyStopping(patience=20, criterion='valid_accuracy', criterion_smaller_is_better=False)],
    batch_iterator_train=FlipBatchIterator(batch_size=100)
)
