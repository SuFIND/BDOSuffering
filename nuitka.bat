nuitka ^
--mingw64 ^
--standalone ^
--show-progress ^
--show-memory ^
--plugin-enable=pyqt6 ^
--nofollow-import-to=cv2,torch,torchvision,PIL,onnxruntime ^
--output-dir=out ^
--disable-console ^
--windows-uac-admin ^
--company-name=SuFIND.Co ^
--product-name=BDOSuffering ^
--file-version=0.0.1 ^
--windows-icon-from-ico=gui_resource\icon.png ^
--include-data-dir=config=config ^
--include-data-dir=third_part=third_part ^
--output-dir=dist start.py