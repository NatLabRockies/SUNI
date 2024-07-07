#####################################################################################################################
#
# CMake and System Settings
#
#####################################################################################################################

cmake_minimum_required(VERSION 3.24)

set(CMAKE_OSX_DEPLOYMENT_TARGET "10.15" CACHE STRING "Minimum OS X deployment version")

set(CMAKE_XCODE_ATTRIBUTE_OTHER_CODE_SIGN_FLAGS "-o linker-signed")

if (UNIX AND NOT CMAKE_C_COMPILER)
	set(CMAKE_C_COMPILER gcc)
	set(CMAKE_CXX_COMPILER g++)
endif()


#####################################################################################################################
#
# Project Settings
#
#####################################################################################################################


set(SUNI_SRC 
    src/main.cpp                    src/main.h
    src/csv.cpp                     src/csv.h
    src/pythonhandler.cpp           src/pythonhandler.h
)


#####################################################################################################################
#
# Compile Options per Platform
#
#####################################################################################################################

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(MSVC)
	add_compile_options(/W4 /MP)
	foreach (flag_var CMAKE_C_FLAGS_DEBUG CMAKE_CXX_FLAGS_DEBUG)
		set(${flag_var} "${${flag_var}} /D_DEBUG" CACHE STRING "compile flags" FORCE)
	endforeach()
	add_compile_definitions( _CRT_SECURE_NO_WARNINGS _MBCS __WXMSW__ __64BIT__)
	foreach (flag_var CMAKE_C_FLAGS_DEBUG CMAKE_CXX_FLAGS_DEBUG)
		set(${flag_var} "${${flag_var}} /D_DEBUG" CACHE STRING "compile flags" FORCE)
	endforeach()
else(MSVC)
	if (APPLE)
		add_definitions(-DWX_PRECOMP)
	else()
		add_compile_options(-Wno-deprecated)
	endif()
	add_compile_options(-Wall -Wno-unknown-pragmas -Wno-overloaded-virtual -std=c++11)
	if(CMAKE_BUILD_TYPE STREQUAL "Debug")
		add_compile_definitions(_DEBUG)
	else()
		add_compile_options(-O3 -DNDEBUG)
	endif()
endif(MSVC)
add_compile_options(${wxWidgets_CXX_FLAGS})
add_definitions(-DLK_USE_WXWIDGETS )



#####################################################################################################################
#
# Packages
#
#####################################################################################################################

if (UNIX)
    if (EXISTS /usr/local/bin/wx-config-3)
        set(wxWidgets_CONFIG_EXECUTABLE /usr/local/bin/wx-config-3)
    else ()
        set(wxWidgets_CONFIG_EXECUTABLE $ENV{WXMSW3}/bin/wx-config)
    endif ()

    if (APPLE)
        find_package(wxWidgets REQUIRED xrc webview stc richtext ribbon propgrid aui gl html qa adv core xml net base )
    else()
	    find_package(wxWidgets REQUIRED xrc stc richtext ribbon propgrid aui gl html qa adv core xml net base )
    endif()
else()
	set(wxWidgets_ROOT_DIR $ENV{WXMSW3})
	find_package(wxWidgets REQUIRED xrc webview stc richtext ribbon propgrid aui gl html qa adv core xml net base scintilla)
endif()

include(${wxWidgets_USE_FILE})


#####################################################################################################################
#
# CMake Targets
#
#####################################################################################################################

# Setup Application
# setup icons if desired
if (APPLE)
	set(MACOSX_BUNDLE_ICON_FILE SAM.icns)
	set(SUNI_ICON ${CMAKE_CURRENT_SOURCE_DIR}/build_resources/SUNI.icns)
	set_source_files_properties(${SUNI_ICON} PROPERTIES
		MACOSX_PACKAGE_LOCATION "Resources")
elseif(WIN32)
	set(SUNI_ICON ${CMAKE_CURRENT_SOURCE_DIR}/build_resources/SUNI.rc)
endif()

# have to make executables with different names so the .app's have different names
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
	add_executable(SUNId
			WIN32
			MACOSX_BUNDLE
			${SUNI_SRC}
            ${SUNI_ICON})
	set(SUNI_EXE SUNId)
else() # if Release or if MSVC multigenerator
	add_executable(SUNI
			WIN32
			MACOSX_BUNDLE
			${SUNI_SRC}
            ${SUNI_ICON})
	set(SUNI_EXE SUNI)
endif()

if (MSVC)
	set_target_properties(${SUNI_EXE}
		PROPERTIES
		LINK_FLAGS /SUBSYSTEM:WINDOWS)
#        DEBUG_POSTFIX "d"
#		RUNTIME_OUTPUT_DIRECTORY $<1:${CMAKE_CURRENT_SOURCE_DIR}>/deploy/x64)
else()
    if(CMAKE_BUILD_TYPE STREQUAL "Debug")
        set(SUNI_NAME SUNId)
    else()
        set(SUNI_NAME SUNI)
    endif()
    if(APPLE)
        if (CMAKE_GENERATOR STREQUAL Xcode)
            if(CMAKE_BUILD_TYPE STREQUAL "Debug")
                set(SUNI_APP ${CMAKE_CURRENT_BINARY_DIR}/Debug/${SUNI_NAME}.app)
            else()
                set(SUNI_APP ${CMAKE_CURRENT_BINARY_DIR}/Release/${SUNI_NAME}.app)
            endif()
        else()
            set(SUNI_APP ${CMAKE_CURRENT_BINARY_DIR}/${SUNI_NAME}.app)
        endif()
    else()
        set(SUNI_APP ${CMAKE_CURRENT_BINARY_DIR}/deploy)
        set_target_properties(${SUNI_EXE}
                PROPERTIES
                OUTPUT_NAME ${SUNI_NAME}.bin
                RUNTIME_OUTPUT_DIRECTORY ${SUNI_APP}/linux_64)
    endif()
endif()

#####################################################################################################################
#
# Link Libraries and Options
#
#####################################################################################################################


target_link_libraries(${SUNI_EXE} ${wxWidgets_LIBRARIES})


#####################################################################################################################
#
# Target Installation
#
#####################################################################################################################

SET(CMAKE_SKIP_BUILD_RPATH)

if (UNIX)
    if (APPLE)
        file(TO_CMAKE_PATH $ENV{SUNINRELDIR} SUNINRELDIR)

        add_custom_command(
            TARGET ${SUNI_EXE}
            POST_BUILD
            COMMAND rsync -a -v "${SUNINRELDIR}/deploy/Configuration Files" ${SUNI_APP}/Contents/MacOS
            COMMAND rsync -a -v "${SUNINRELDIR}/deploy/System Files" ${SUNI_APP}/Contents/MacOS
            COMMAND rsync -a -v "${SUNINRELDIR}/deploy/Instrument Files" ${SUNI_APP}/Contents/MacOS
            COMMAND rsync -a -v ${CMAKE_CURRENT_SOURCE_DIR}/python/* ${SUNI_APP}/Contents/MacOS
            COMMAND cp ${CMAKE_CURRENT_SOURCE_DIR}/build_resources/Info-${SUNI_NAME}.plist ${SUNI_APP}/Contents/Info.plist
#            COMMAND mkdir -p ${SUNI_APP}/Contents/Frameworks
#            COMMAND install_name_tool -change ${SSC_NAME} @executable_path/../Frameworks/${SSC_NAME} ${SUNI_APP}/Contents/MacOS/${SAM_NAME}
        )
    else()
        add_custom_command(
                TARGET ${SAM_EXE}
                PRE_BUILD
                COMMAND rm -rf ${SUNI_APP}/linux_64
                COMMAND mkdir -p ${SUNI_APP}/linux_64
        )
        add_custom_command(
                TARGET ${SAM_EXE}
                POST_BUILD
                COMMAND rsync -a -v ${CMAKE_CURRENT_SOURCE_DIR}/deploy/* ${SUNI_APP}
                COMMAND cp ${SSC_SO} ${SUNI_APP}/linux_64
        )

    endif()
else()
# type cannot be used in set statement

    file(TO_CMAKE_PATH $ENV{SUNINRELDIR} SUNINRELDIR)
 
    set( DEPLOY_FOLDERS
        "System Files"
        "Configuration Files"
        "Instrument Files"
    )

    #CMAKE requires extra manipulation with Debug and Release builds
    foreach( folder_i ${DEPLOY_FOLDERS})
        add_custom_command(
        TARGET ${SUNI_EXE}
        PRE_BUILD
        COMMAND ${CMAKE_COMMAND}
        ARGS -E copy_directory ${SUNINRELDIR}/deploy/${folder_i} ${CMAKE_CURRENT_BINARY_DIR}/Debug/${folder_i}
    )
   endforeach( folder_i )
   foreach( folder_i ${DEPLOY_FOLDERS})
        add_custom_command(
        TARGET ${SUNI_EXE}
        PRE_BUILD
        COMMAND ${CMAKE_COMMAND}
        ARGS -E copy_directory ${SUNINRELDIR}/deploy/${folder_i} ${CMAKE_CURRENT_BINARY_DIR}/Release/${folder_i}
    )
    endforeach( folder_i )

#    set( PYTHON_FOLDERS
#        "SUNI"
#        "SERIQC"
#    )
#    set (SYSTEM_FILES "System Files")

    #CMAKE requires extra manipulation with Debug and Release builds
#    foreach( folder_i ${PYTHON_FOLDERS})
#        add_custom_command(
#        TARGET ${SUNI_EXE}
#        PRE_BUILD
#        COMMAND ${CMAKE_COMMAND}
#        ARGS -E copy_directory ${SUNINRELDIR}/python/${folder_i} ${CMAKE_CURRENT_BINARY_DIR}/Debug/${SYSTEM_FILES}/${folder_i}
#    )
#   endforeach( folder_i )
#   foreach( folder_i ${PYTHON_FOLDERS})
#        add_custom_command(
#        TARGET ${SUNI_EXE}
#        PRE_BUILD
#        COMMAND ${CMAKE_COMMAND}
#        ARGS -E copy_directory ${SUNINRELDIR}/python/${folder_i} ${CMAKE_CURRENT_BINARY_DIR}/Release/${SYSTEM_FILES}/${folder_i}
#    )
#    endforeach( folder_i )


endif()

