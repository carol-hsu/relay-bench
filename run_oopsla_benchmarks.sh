#!/bin/bash
dest_dir=$1

# have to run TF by itself first because it hogs all the GPU memory
# otherwise
python3 oopsla_benchmarks/cnn_trials.py --n-times-per-input 10 --skip-pytorch --skip-relay --skip-nnvm --skip-mxnet --output-dir "${dest_dir}"
# now run everything besides TF
python3 oopsla_benchmarks/cnn_trials.py --n-times-per-input 10 --skip-tf --output-dir "${dest_dir}"

# Only running RNNs on CPU because GPU has not been implemented for Pytorch example
# Skip gluon RNNs because the MxNet importer needs to be updated

# We run char RNN separately because the AoT compiler runs out of
# system memory if we launch it too many times in the same Python processes
# (just a precaution)

python3 oopsla_benchmarks/rnn_trials.py --n-times-per-input 10 --no-gpu --skip-gluon-rnns --skip-treelstm --output-dir "${dest_dir}"

python3 oopsla_benchmarks/rnn_trials.py --n-times-per-input 10 --no-gpu --skip-gluon-rnns --skip-char-rnn --output-dir "${dest_dir}"