SRCDIR = ./src
RESOURCEDIR = ./resource
DEPLOYDIR = ./deploy
VPATH = $(SRCDIR)


SUNIDIR = ../../SUNI
BUILDDIR = ../../build/Release

TARGET = SUNI

all: setup makes app 


setup:
	rm -rf $(SRCDIR)
	mkdir -p $(SRCDIR)
	rm -rf $(SRCDIR)/rapidjson
	mkdir -p $(SRCDIR)/rapidjson
	rm -rf $(RESOURCEDIR)
	mkdir -p $(RESOURCEDIR)
	rm -rf $(DEPLOYDIR)
	mkdir -p $(DEPLOYDIR)
	cp -Rv $(SUNIDIR)/src/* $(SRCDIR)
#	cp $(SUNIDIR)/src/rapidjson/* $(SRCDIR)/rapidjson
	cp $(SUNIDIR)/build_resources/* $(RESOURCEDIR)
#	cp ../src/* $(SRCDIR)
	cp -Rv $(SUNIDIR)/deploy ./
	cp -Rv ../deploy ./



makes:
	 make -f Makefile-SUNI ARCH=arm64 -j8
	 rm *.d
	 rm *.o
	 make -f Makefile-SUNI ARCH=x86_64 -j8
	 rm *.d
	 rm *.o

app:
	lipo -create -output $(TARGET) SUNI_x86_64 SUNI_arm64 
	mkdir -p $(TARGET).app
	mkdir -p $(TARGET).app/Contents
	mkdir -p $(TARGET).app/Contents/MacOS
	mkdir -p $(TARGET).app/Contents/Resources
	mkdir -p $(TARGET).app/Contents/runtime
#	make -f Makefile-webupd
	python copy_runtime.py
	cp $(TARGET) ./$(TARGET).app/Contents/MacOS
	cp resource/$(TARGET).icns ./$(TARGET).app/Contents/Resources
	cp resource/Info-$(TARGET).plist ./$(TARGET).app/Contents/Info.plist
	echo "-n APPL????" >> ./$(TARGET).app/Contents/PkgInfo
#	install_name_tool -add_rpath @executable_path/../Frameworks/ ${TARGET}.app/Contents/MacOS/${TARGET}
	# this signs for testing purposes. Must sign with Application ID to prevent gatekeeper message and opening issues.
	codesign --force --deep --sign - ./${TARGET}.app


clean:
	rm -f *.o
	rm -f *.d
	rm -rf ${TARGET}.app 
	rm -f ${TARGET}_x86_64 ${TARGET}_arm64
