# FlipperToolkit

Простые утилиты для взаимодействия с flipper zero 

## Build
``` bash
git clone https://github.com/apfxtech/FlipperToolkit.git
cd FlipperToolkit
python3 -m venv venv
source venv/bin/activate
git clone https://github.com/flipperdevices/flipperzero_protobuf_py.git
cd flipperzero_protobuf_py
pip install -r requirements.txt
pip install setuptools
python3 setup.py install
cd ..
```

## GUI 

Отображение окна на движке `pygame`.
``` bash
python3 flipper_cv.py
```

Отображение окна на движке `opencv`.
``` bash
python3 flipper_cv.py screen.mp4
```