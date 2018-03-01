import math
import numpy
import connectors
from matplotlib import pyplot

sampling_rate = 44100.0


class LinearSystem:
    def __init__(self, impulse_response):
        self.__impulse_response = impulse_response
        self.__input = None

    @connectors.Input("get_output")
    def set_input(self, signal):
        self.__input = signal

    @connectors.Output()
    def get_output(self):
        return numpy.convolve(self.__input, self.__impulse_response, mode="full")[0:len(self.__input)]


class SweepGenerator:
    def __init__(self, start_frequency=20.0, stop_frequency=20000.0, length=2 ** 16):
        self.__start_frequency = start_frequency
        self.__stop_frequency = stop_frequency
        self.__length = length

    @connectors.Input("get_sweep")
    def set_start_frequency(self, frequency):
        self.__start_frequency = frequency

    @connectors.Output()
    def get_sweep(self):
        f0 = self.__start_frequency
        fT = self.__stop_frequency
        T = self.__length / sampling_rate               # the duration of the signal
        t = numpy.arange(0.0, T, 1.0 / sampling_rate)   # an array with the time samples
        k = (fT - f0) / T                               # the "sweep rate"
        return numpy.sin(2.0 * math.pi * f0 * t + math.pi * k * (t ** 2))


class FourierTransform:
    def __init__(self, signal=None):
        self.__signal = signal

    @connectors.Input("get_spectrum")
    def set_signal(self, signal):
        self.__signal = signal

    @connectors.Output()
    def get_spectrum(self):
        spectrum = numpy.fft.rfft(self.__signal)
        self.__signal = None
        return spectrum


class TransferFunction:
    def __init__(self, excitation=None, response=None):
        self.__excitation = excitation
        self.__response = response

    @connectors.Input("get_transfer_function")
    def set_excitation(self, signal):
        self.__excitation = signal

    @connectors.Input("get_transfer_function")
    def set_response(self, signal):
        self.__response = signal

    @connectors.Output()
    def get_transfer_function(self):
        return numpy.divide(self.__response, self.__excitation)


class MagnitudePlot:
    def __init__(self):
        self.__spectrums = connectors.MultiInputData()

    @connectors.MultiInput("show")
    def add_spectrum(self, spectrum):
        return self.__spectrums.add(spectrum)

    @add_spectrum.remove
    def remove_spectrum(self, data_id):
        del self.__spectrums[data_id]

    @add_spectrum.replace
    def replace_spectrum(self, data_id, spectrum):
        self.__spectrums[data_id] = spectrum

    @connectors.Output(parallelization=connectors.Parallelization.SEQUENTIAL)
    def show(self):
        for d in self.__spectrums:
            x_axis_data = numpy.linspace(0.0, sampling_rate / 2.0, len(self.__spectrums[d]))
            magnitude = numpy.abs(self.__spectrums[d])
            pyplot.plot(x_axis_data, magnitude)
        pyplot.loglog()
        pyplot.xlim(20.0, sampling_rate / 2.0)
        pyplot.grid(b=True, which="both")
        pyplot.show()


if __name__ == "__main__":
    impulse_response = numpy.zeros(2 ** 16)
    impulse_response[0:3] = (-1.0, 0.0, 1.0)
    system = LinearSystem(impulse_response)

    sweep = SweepGenerator().get_sweep.connect(system.set_input)

    excitation_fft = FourierTransform().set_signal.connect(sweep.get_sweep)
    response_fft = FourierTransform().set_signal.connect(system.get_output)

    transfer_function = TransferFunction()
    transfer_function.set_excitation.connect(excitation_fft.get_spectrum)
    transfer_function.set_response.connect(response_fft.get_spectrum)

    magnitude_plot = MagnitudePlot()
    magnitude_plot.add_spectrum(FourierTransform(impulse_response).get_spectrum())
    transfer_function.get_transfer_function.connect(magnitude_plot.add_spectrum)
    magnitude_plot.show()

    sweep.set_start_frequency(1000.0)
    magnitude_plot.show()
