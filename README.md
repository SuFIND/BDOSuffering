# BDOSuffering
Flesh and blood suffering, can replace by mechanical.

## install
python3.9 + **windows only**
1. cpu platform
    ```shell
    pip install -r requirements.txt
    pip install -r requirements-cpu.txt
    ```
2. gpu platform cuda 11.4
    ```shell
    pip install -r requirements.txt
    pip install -r requirements-gpu.txt
    ```
    cuda or other tools version u can ref [this page](https://onnxruntime.ai/docs/execution-providers/). cuda 11.4 has been tested can work it</br>

## QuickStart
```shell
python start.py
```

## Changelog
- 2023/02/23 
   - Add save or load your config. 
   - You can customize game screen collection in the TimeTab now.
   - Add email alarm when GM check. 😁