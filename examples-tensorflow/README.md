# Set up this environemnt

```sh
cd tf-keras-examples
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

For working with VS code, is may also be worth registering the environment:

```sh
python -m ipykernel install --user --name=snippy-tf-keras-examples --display-name="Python (Snippy - tf keras)"
```

# Installing Tensorflow

```
pip install --upgrade tensorflow

# for GPU support (Nvidia GPU only)
pip install --upgrade tensorflow[and-cuda]
```

## About GPU support on Mac

You cannot directly use CUDA on a Mac with an M2 processor:

- CUDA is NVIDIA Technology: CUDA (Compute Unified Device Architecture) is a parallel computing platform and API developed by NVIDIA. It's designed to work specifically with NVIDIA GPUs.
- Macs Use Apple Silicon: Macs with M2 chips (and other Apple Silicon) use Apple's own GPUs, which have a different architecture. Apple Silicon GPUs are not compatible with CUDA.

Apple has developed its own framework for GPU computing called Metal: This is Apple's API for accessing the GPU on macOS and iOS devices. TensorFlow has been optimized to work with Apple's Metal framework. This allows TensorFlow to utilize the GPU for accelerated computation, but it's not CUDA.  
When you install TensorFlow on a Mac with Apple Silicon, Tensorflow is therefore configured to use the Metal Performance Shaders (MPS) backend.
