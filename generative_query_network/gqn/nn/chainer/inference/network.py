import chainer
import chainer.functions as cf
import cupy
import math

from ... import base
from .parameters import Parameters


class Network(base.inference.Network):
    def __init__(self, params):
        assert isinstance(params, Parameters)
        self.params = params

    def forward_onestep(self, prev_h_g, prev_h_e, prev_c_e, x, v, r):
        broadcast_shape = (
            prev_h_e.shape[0],
            v.shape[1],
        ) + prev_h_e.shape[2:]
        v = cf.reshape(v, v.shape + (1, 1))
        v = cf.broadcast_to(v, shape=broadcast_shape)

        x = cf.relu(self.params.conv_x_1(x))
        x = cf.relu(self.params.conv_x_2(x))

        lstm_in = cf.concat((prev_h_e, prev_h_g, x, v, r), axis=1)
        forget_gate = cf.sigmoid(self.params.lstm_f(lstm_in))
        input_gate = cf.sigmoid(self.params.lstm_i(lstm_in))
        next_c = forget_gate * prev_c_e + input_gate * cf.tanh(
            self.params.lstm_tanh(lstm_in))
        next_h = cf.sigmoid(self.params.lstm_o(lstm_in)) * cf.tanh(next_c)
        return next_h, next_c

    def compute_mu_z(self, h):
        xp = cupy.get_array_module(h.data)
        mean = self.params.mean_z(h)
        return mean

    def sample_z(self, h):
        xp = cupy.get_array_module(h.data)
        mean = self.compute_mu_z(h)
        return cf.gaussian(mean, xp.zeros_like(mean))
