import numpy as np

from nn.base import BaseNeuralNet
from nn.modules import Convolution, Linear
from tools.activations import MaxPooling, Sigmoid, Softmax
from loss.classification import cross_entropy


class SingleCNN(BaseNeuralNet):
    def __init__(self, input_dim, output_dim: int, kernel_dim: tuple , padding: str, pooling_size: int):
        super().__init__()
        self.cnn = Convolution(
            input_dim=input_dim,
            kernel_dim=kernel_dim,
            padding = padding
        )
        n, _, _ = input_dim
        self.max_pooling = MaxPooling(input_dim=(n, self.cnn.h_out, self.cnn.w_out),
                                      k=pooling_size)
        self.sigmoid = Sigmoid()
        self.softmax = Softmax()

        h_out = self.max_pooling.h_out
        w_out = self.max_pooling.w_out
        self.fc = Linear(input_dim=h_out*w_out, output_dim=output_dim)

        self.gradient_step_layers = [self.cnn, self.fc]

    def forward(self, x):
        n, h_in, w_in = x.shape
        x = self.cnn.forward(x) # (n, h_out, w_out)
        x = self.max_pooling.forward(x) # (n, h_out // k, w_out // k)
        x = self.sigmoid.forward(x)
        x = self.fc.forward(x.reshape(n,-1)) # (n, h_out*w_out) -> (n, out_dim)
        x = self.softmax.forward(x)
        return x

    def backward(self, y, pred, X):
        """
        params
        ------
        y: np.ndarray (n, n_label)
            One hot encoded vector for class label

        pred: np.ndarray (n, n_label)
            Probability of each class, whose row sum is equal to 1

        X: np.ndarray (n, h_in, w_in)
            Arrary of input images
        """
        n, _ = y.shape
        dhaty = self.softmax.backward(y) # (n, n_label)
        dx = self.fc.backward(dhaty) # (n, h_in)
        dx = self.max_pooling.backward(dx.reshape(n, self.max_pooling.h_out, -1)) # (n, h_in, w_in)
        dx = self.cnn.backward(dx) # (n, h_in, w_in)
        return dx

    def step(self, lr):
        for layer in self.gradient_step_layers:
            params_info = layer.get_params_grad()
            for param,info in params_info.items():
                param_grad_step = info["current"] - lr*info["grad"]
                setattr(layer, param, param_grad_step)

    def zero_grad(self):
        pass

if __name__ == "__main__":
    from sklearn.datasets import fetch_openml

    mnist = fetch_openml('mnist_784', as_frame=False)
    X = [x.reshape(28, -1) for x in mnist.data]
    h = X[0].shape[0]
    target = [int(i) for i in mnist.target]
    num_label = len(np.unique(target))
    one_hot_target = np.eye(num_label)[target]
    epoch = 100

    for i in range(epoch):

        loss = 0
        correct = 0

        for x,y in zip(X, one_hot_target):
            y_prob_pred = cnn.forward(x)
            y_pred = y_prob_pred.argmax()

            correct += (y_pred == y.argmax())
            loss += cross_entropy(y, y_prob_pred)

        print(f"epoch {epoch}: {round(loss, 4)} loss / {round(correct / len(X), 4)} accuracy")

        break