<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="25008000">
	<Property Name="NI.LV.All.SourceOnly" Type="Bool">true</Property>
	<Property Name="NI.Project.Description" Type="Str">RemoteVI - publish a LabVIEW front panel to a web browser, pixel-accurate and interactive.</Property>
	<Item Name="My Computer" Type="My Computer">
		<Property Name="server.app.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.control.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.tcp.enabled" Type="Bool">false</Property>
		<Property Name="server.tcp.port" Type="Int">0</Property>
		<Property Name="server.tcp.serviceName" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.tcp.serviceName.default" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.vi.callsEnabled" Type="Bool">true</Property>
		<Property Name="server.vi.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="specify.custom.address" Type="Bool">false</Property>
		<Item Name="RemoteVI.lvlib" Type="Library" URL="../source/RemoteVI.lvlib"/>
		<Item Name="Examples" Type="Folder">
			<Item Name="RemoteVI Demo Layout.vi" Type="VI" URL="../examples/RemoteVI Demo Layout.vi"/>
			<Item Name="RemoteVI Demo.vi" Type="VI" URL="../examples/RemoteVI Demo.vi"/>
		</Item>
		<Item Name="Scripts" Type="Folder">
			<Item Name="Win32 Wrapper Builder" Type="Folder">
				<Item Name="W32B Build Wrapper.vi" Type="VI" URL="../scripts/Win32 Wrapper Builder/W32B Build Wrapper.vi"/>
				<Item Name="W32B Create CLFN.vi" Type="VI" URL="../scripts/Win32 Wrapper Builder/W32B Create CLFN.vi"/>
				<Item Name="W32B Ensure Folder.vi" Type="VI" URL="../scripts/Win32 Wrapper Builder/W32B Ensure Folder.vi"/>
				<Item Name="W32B Find Control Terminal.vi" Type="VI" URL="../scripts/Win32 Wrapper Builder/W32B Find Control Terminal.vi"/>
				<Item Name="W32B Find Node Terminal.vi" Type="VI" URL="../scripts/Win32 Wrapper Builder/W32B Find Node Terminal.vi"/>
				<Item Name="W32B Parse Spec.vi" Type="VI" URL="../scripts/Win32 Wrapper Builder/W32B Parse Spec.vi"/>
			</Item>
			<Item Name="Win32 Wrapper Templates" Type="Folder">
				<Item Name="AttachThreadInput Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/AttachThreadInput Wrapper Template.vi"/>
				<Item Name="BCryptGenRandom Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/BCryptGenRandom Wrapper Template.vi"/>
				<Item Name="BitBlt Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/BitBlt Wrapper Template.vi"/>
				<Item Name="ChildWindowFromPointEx Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/ChildWindowFromPointEx Wrapper Template.vi"/>
				<Item Name="CloseHandle Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/CloseHandle Wrapper Template.vi"/>
				<Item Name="CreateCompatibleBitmap Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/CreateCompatibleBitmap Wrapper Template.vi"/>
				<Item Name="CreateCompatibleDC Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/CreateCompatibleDC Wrapper Template.vi"/>
				<Item Name="CreateRectRgn Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/CreateRectRgn Wrapper Template.vi"/>
				<Item Name="DeleteDC Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/DeleteDC Wrapper Template.vi"/>
				<Item Name="DeleteObject Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/DeleteObject Wrapper Template.vi"/>
				<Item Name="FindWindowExW Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/FindWindowExW Wrapper Template.vi"/>
				<Item Name="GetAncestor Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetAncestor Wrapper Template.vi"/>
				<Item Name="GetClassNameW Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetClassNameW Wrapper Template.vi"/>
				<Item Name="GetClientRect Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetClientRect Wrapper Template.vi"/>
				<Item Name="GetCurrentProcessId Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetCurrentProcessId Wrapper Template.vi"/>
				<Item Name="GetCurrentThreadId Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetCurrentThreadId Wrapper Template.vi"/>
				<Item Name="GetCursorPos Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetCursorPos Wrapper Template.vi"/>
				<Item Name="GetDC Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetDC Wrapper Template.vi"/>
				<Item Name="GetDIBits Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetDIBits Wrapper Template.vi"/>
				<Item Name="GetGUIThreadInfo Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetGUIThreadInfo Wrapper Template.vi"/>
				<Item Name="GetKeyboardState Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetKeyboardState Wrapper Template.vi"/>
				<Item Name="GetSysColor Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetSysColor Wrapper Template.vi"/>
				<Item Name="GetWindow Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetWindow Wrapper Template.vi"/>
				<Item Name="GetWindowLongPtrW Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetWindowLongPtrW Wrapper Template.vi"/>
				<Item Name="GetWindowRect Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetWindowRect Wrapper Template.vi"/>
				<Item Name="GetWindowTextW Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetWindowTextW Wrapper Template.vi"/>
				<Item Name="GetWindowThreadProcessId Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/GetWindowThreadProcessId Wrapper Template.vi"/>
				<Item Name="IsIconic Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/IsIconic Wrapper Template.vi"/>
				<Item Name="IsWindow Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/IsWindow Wrapper Template.vi"/>
				<Item Name="IsWindowEnabled Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/IsWindowEnabled Wrapper Template.vi"/>
				<Item Name="IsWindowVisible Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/IsWindowVisible Wrapper Template.vi"/>
				<Item Name="OpenProcess Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/OpenProcess Wrapper Template.vi"/>
				<Item Name="PostMessageW Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/PostMessageW Wrapper Template.vi"/>
				<Item Name="PrintWindow Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/PrintWindow Wrapper Template.vi"/>
				<Item Name="QueryFullProcessImageNameW Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/QueryFullProcessImageNameW Wrapper Template.vi"/>
				<Item Name="ReleaseDC Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/ReleaseDC Wrapper Template.vi"/>
				<Item Name="ScreenToClient Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/ScreenToClient Wrapper Template.vi"/>
				<Item Name="SelectObject Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/SelectObject Wrapper Template.vi"/>
				<Item Name="SendMessageTimeoutW Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/SendMessageTimeoutW Wrapper Template.vi"/>
				<Item Name="SetKeyboardState Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/SetKeyboardState Wrapper Template.vi"/>
				<Item Name="SetLayeredWindowAttributes Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/SetLayeredWindowAttributes Wrapper Template.vi"/>
				<Item Name="SetWindowLongPtrW Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/SetWindowLongPtrW Wrapper Template.vi"/>
				<Item Name="SetWindowPos Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/SetWindowPos Wrapper Template.vi"/>
				<Item Name="SetWindowRgn Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/SetWindowRgn Wrapper Template.vi"/>
				<Item Name="ShowWindow Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/ShowWindow Wrapper Template.vi"/>
			</Item>
			<Item Name="Build Win32 Wrappers.vi" Type="VI" URL="../scripts/Build Win32 Wrappers.vi"/>
		</Item>
		<Item Name="Spikes" Type="Folder">
			<Item Name="Bench Dirty Rects.vi" Type="VI" URL="../spikes/Bench Dirty Rects.vi"/>
			<Item Name="Bench Encode PNG.vi" Type="VI" URL="../spikes/Bench Encode PNG.vi"/>
			<Item Name="Spike Start Errors.vi" Type="VI" URL="../spikes/Spike Start Errors.vi"/>
		</Item>
		<Item Name="Tests" Type="Folder">
			<Item Name="Caraya" Type="Folder">
				<Item Name="support" Type="Folder">
					<Item Name="RemoteVI Check Dirty Rects.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Dirty Rects.vi"/>
					<Item Name="RemoteVI Check Format Duration.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Format Duration.vi"/>
					<Item Name="RemoteVI Check Frame Encode.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Frame Encode.vi"/>
					<Item Name="RemoteVI Check JSON String.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check JSON String.vi"/>
					<Item Name="RemoteVI Check Landing Page.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Landing Page.vi"/>
					<Item Name="RemoteVI Check Next Free Port.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Next Free Port.vi"/>
					<Item Name="RemoteVI Check Overlay Encode.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Overlay Encode.vi"/>
					<Item Name="RemoteVI Check Parse Arguments.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Parse Arguments.vi"/>
					<Item Name="RemoteVI Check Parse Input.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Parse Input.vi"/>
					<Item Name="RemoteVI Check Splitters Message.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Splitters Message.vi"/>
					<Item Name="RemoteVI Check Status Convert.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Status Convert.vi"/>
					<Item Name="RemoteVI Check Status Text.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Status Text.vi"/>
					<Item Name="RemoteVI Check Tips Message.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Tips Message.vi"/>
					<Item Name="RemoteVI Check Token Check.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Token Check.vi"/>
					<Item Name="RemoteVI Check Track Modifiers.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Track Modifiers.vi"/>
					<Item Name="RemoteVI Check Translate Input.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Translate Input.vi"/>
					<Item Name="RemoteVI Check Window Frame Encode.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Window Frame Encode.vi"/>
					<Item Name="RemoteVI Check Window Rows.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Window Rows.vi"/>
					<Item Name="RemoteVI Check WS Decode Client Frame.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check WS Decode Client Frame.vi"/>
					<Item Name="RemoteVI Check WS Encode Server Frame.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check WS Encode Server Frame.vi"/>
					<Item Name="RemoteVI Test Bytes To Hex.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Test Bytes To Hex.vi"/>
					<Item Name="RemoteVI Test Hex To Bytes.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Test Hex To Bytes.vi"/>
				</Item>
				<Item Name="unit" Type="Folder">
					<Item Name="App" Type="Folder">
						<Item Name="Test Landing Page.vi" Type="VI" URL="../tests/caraya/unit/App/Test Landing Page.vi"/>
						<Item Name="Test Next Free Port.vi" Type="VI" URL="../tests/caraya/unit/App/Test Next Free Port.vi"/>
						<Item Name="Test Parse Arguments.vi" Type="VI" URL="../tests/caraya/unit/App/Test Parse Arguments.vi"/>
						<Item Name="Test Window Rows.vi" Type="VI" URL="../tests/caraya/unit/App/Test Window Rows.vi"/>
					</Item>
					<Item Name="Capture" Type="Folder">
						<Item Name="Test Dirty Rects.vi" Type="VI" URL="../tests/caraya/unit/Capture/Test Dirty Rects.vi"/>
					</Item>
					<Item Name="Input" Type="Folder">
						<Item Name="Test Track Modifiers.vi" Type="VI" URL="../tests/caraya/unit/Input/Test Track Modifiers.vi"/>
						<Item Name="Test Translate Input.vi" Type="VI" URL="../tests/caraya/unit/Input/Test Translate Input.vi"/>
					</Item>
					<Item Name="Protocol" Type="Folder">
						<Item Name="Test Frame Encode.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test Frame Encode.vi"/>
						<Item Name="Test JSON String.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test JSON String.vi"/>
						<Item Name="Test Overlay Encode.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test Overlay Encode.vi"/>
						<Item Name="Test Parse Input.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test Parse Input.vi"/>
						<Item Name="Test Splitters Message.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test Splitters Message.vi"/>
						<Item Name="Test Tips Message.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test Tips Message.vi"/>
						<Item Name="Test Window Frame Encode.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test Window Frame Encode.vi"/>
						<Item Name="Test WS Decode Client Frame.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test WS Decode Client Frame.vi"/>
						<Item Name="Test WS Encode Server Frame.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test WS Encode Server Frame.vi"/>
					</Item>
					<Item Name="Server" Type="Folder">
						<Item Name="Test Format Duration.vi" Type="VI" URL="../tests/caraya/unit/Server/Test Format Duration.vi"/>
						<Item Name="Test Status Convert.vi" Type="VI" URL="../tests/caraya/unit/Server/Test Status Convert.vi"/>
						<Item Name="Test Status Text.vi" Type="VI" URL="../tests/caraya/unit/Server/Test Status Text.vi"/>
						<Item Name="Test Token Check.vi" Type="VI" URL="../tests/caraya/unit/Server/Test Token Check.vi"/>
					</Item>
				</Item>
				<Item Name="RemoteVI Caraya Runner.vi" Type="VI" URL="../tests/caraya/RemoteVI Caraya Runner.vi"/>
			</Item>
			<Item Name="Fixture" Type="Folder">
				<Item Name="build" Type="Folder">
					<Item Name="Fixture Tab Panel.vi" Type="VI" URL="../tests/fixtures/build/Fixture Tab Panel.vi"/>
				</Item>
				<Item Name="RemoteVI Complex Fixture All Controls.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex Fixture All Controls.vi"/>
				<Item Name="RemoteVI Complex Fixture Arrange.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex Fixture Arrange.vi"/>
				<Item Name="RemoteVI Complex Fixture Button Refs.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex Fixture Button Refs.vi"/>
				<Item Name="RemoteVI Complex Fixture Children.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex Fixture Children.vi"/>
				<Item Name="RemoteVI Complex Fixture Events.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex Fixture Events.vi"/>
				<Item Name="RemoteVI Complex Fixture Find Controls.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex Fixture Find Controls.vi"/>
				<Item Name="RemoteVI Complex Fixture Layout.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex Fixture Layout.vi"/>
				<Item Name="RemoteVI Complex Fixture Paste.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex Fixture Paste.vi"/>
				<Item Name="RemoteVI Complex Fixture Prep Panel.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex Fixture Prep Panel.vi"/>
				<Item Name="RemoteVI Complex Fixture Refs.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex Fixture Refs.vi"/>
				<Item Name="RemoteVI Complex Fixture Value Text.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex Fixture Value Text.vi"/>
				<Item Name="RemoteVI Complex Fixture.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex Fixture.vi"/>
				<Item Name="RemoteVI Complex Inspector.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex Inspector.vi"/>
				<Item Name="RemoteVI Complex View A.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex View A.vi"/>
				<Item Name="RemoteVI Complex View B.vi" Type="VI" URL="../tests/fixtures/RemoteVI Complex View B.vi"/>
				<Item Name="RemoteVI Fixture Arrange.vi" Type="VI" URL="../tests/fixtures/RemoteVI Fixture Arrange.vi"/>
				<Item Name="RemoteVI Fixture Find Control.vi" Type="VI" URL="../tests/fixtures/RemoteVI Fixture Find Control.vi"/>
				<Item Name="RemoteVI Fixture Key Line.vi" Type="VI" URL="../tests/fixtures/RemoteVI Fixture Key Line.vi"/>
				<Item Name="RemoteVI Fixture Layout.vi" Type="VI" URL="../tests/fixtures/RemoteVI Fixture Layout.vi"/>
				<Item Name="RemoteVI Fixture Log Path.vi" Type="VI" URL="../tests/fixtures/RemoteVI Fixture Log Path.vi"/>
				<Item Name="RemoteVI Fixture Mods.vi" Type="VI" URL="../tests/fixtures/RemoteVI Fixture Mods.vi"/>
				<Item Name="RemoteVI Fixture Mouse Line.vi" Type="VI" URL="../tests/fixtures/RemoteVI Fixture Mouse Line.vi"/>
				<Item Name="RemoteVI Fixture Value Line.vi" Type="VI" URL="../tests/fixtures/RemoteVI Fixture Value Line.vi"/>
				<Item Name="RemoteVI Fixture.vi" Type="VI" URL="../tests/fixtures/RemoteVI Fixture.vi"/>
			</Item>
		</Item>
		<Item Name="Tools Menu" Type="Folder">
			<Item Name="RemoteVI" Type="Folder">
				<Item Name="Share in Browser.vi" Type="VI" URL="../tools-menu/RemoteVI/Share in Browser.vi"/>
			</Item>
		</Item>
		<Item Name="Dependencies" Type="Dependencies"/>
		<Item Name="Build Specifications" Type="Build">
			<Item Name="RemoteVI Server" Type="EXE">
				<Property Name="App_copyErrors" Type="Bool">true</Property>
				<Property Name="App_INI_aliasGUID" Type="Str">{81C9FC2F-8BC2-548F-9224-E283476CB9FC}</Property>
				<Property Name="App_INI_GUID" Type="Str">{E7C5A895-CC21-5121-919A-CBD575C7FEF9}</Property>
				<Property Name="App_serverConfig.httpPort" Type="Int">8002</Property>
				<Property Name="App_serverType" Type="Int">0</Property>
				<Property Name="Bld_autoIncrement" Type="Bool">false</Property>
				<Property Name="Bld_buildCacheID" Type="Str">{85C2DEC8-5A5A-5251-AED8-F79D3BA02E64}</Property>
				<Property Name="Bld_buildSpecName" Type="Str">RemoteVI Server</Property>
				<Property Name="Bld_excludeInlineSubVIs" Type="Bool">true</Property>
				<Property Name="Bld_excludeLibraryItems" Type="Bool">false</Property>
				<Property Name="Bld_excludePolymorphicVIs" Type="Bool">true</Property>
				<Property Name="Bld_localDestDir" Type="Path">../builds/RemoteVI Server</Property>
				<Property Name="Bld_localDestDirType" Type="Str">relativeToProject</Property>
				<Property Name="Bld_modifyLibraryFile" Type="Bool">true</Property>
				<Property Name="Bld_previewCacheID" Type="Str">{7DAA8E6F-7C7D-57F9-9FC4-AD9EE8AAB827}</Property>
				<Property Name="Bld_version.build" Type="Int">0</Property>
				<Property Name="Bld_version.major" Type="Int">1</Property>
				<Property Name="Destination[0].destName" Type="Str">RemoteVI Server.exe</Property>
				<Property Name="Destination[0].path" Type="Path">../builds/RemoteVI Server/RemoteVI Server.exe</Property>
				<Property Name="Destination[0].path.type" Type="Str">relativeToProject</Property>
				<Property Name="Destination[0].preserveHierarchy" Type="Bool">true</Property>
				<Property Name="Destination[0].type" Type="Str">App</Property>
				<Property Name="Destination[1].destName" Type="Str">Support Directory</Property>
				<Property Name="Destination[1].path" Type="Path">../builds/RemoteVI Server/data</Property>
				<Property Name="Destination[1].path.type" Type="Str">relativeToProject</Property>
				<Property Name="DestinationCount" Type="Int">2</Property>
				<Property Name="Source[0].itemID" Type="Str">{86D3750F-8178-58BF-A4E3-3C5ACAD7BE1D}</Property>
				<Property Name="Source[0].type" Type="Str">Container</Property>
				<Property Name="Source[1].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[1].itemID" Type="Ref">/My Computer/RemoteVI.lvlib/App/RemoteVI Server.vi</Property>
				<Property Name="Source[1].sourceInclusion" Type="Str">TopLevel</Property>
				<Property Name="Source[1].type" Type="Str">VI</Property>
				<Property Name="Source[2].Library.allowMissingMembers" Type="Bool">true</Property>
				<Property Name="Source[2].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[2].itemID" Type="Ref">/My Computer/RemoteVI.lvlib</Property>
				<Property Name="Source[2].sourceInclusion" Type="Str">Include</Property>
				<Property Name="Source[2].type" Type="Str">Library</Property>
				<Property Name="Source[3].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[3].itemID" Type="Ref">/My Computer/RemoteVI.lvlib/Server/RemoteVI Server Loop.vi</Property>
				<Property Name="Source[3].sourceInclusion" Type="Str">Include</Property>
				<Property Name="Source[3].type" Type="Str">VI</Property>
				<Property Name="Source[4].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[4].itemID" Type="Ref">/My Computer/RemoteVI.lvlib/App/RemoteVI Landing Server.vi</Property>
				<Property Name="Source[4].sourceInclusion" Type="Str">Include</Property>
				<Property Name="Source[4].type" Type="Str">VI</Property>
				<Property Name="Source[5].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[5].itemID" Type="Ref">/My Computer/RemoteVI.lvlib/API/RemoteVI Status Panel.vi</Property>
				<Property Name="Source[5].sourceInclusion" Type="Str">Include</Property>
				<Property Name="Source[5].type" Type="Str">VI</Property>
				<Property Name="SourceCount" Type="Int">6</Property>
				<Property Name="TgtF_companyName" Type="Str">Jan Goebel</Property>
				<Property Name="TgtF_enableDebugging" Type="Bool">false</Property>
				<Property Name="TgtF_fileDescription" Type="Str">RemoteVI Server - share any window in a web browser</Property>
				<Property Name="TgtF_internalName" Type="Str">RemoteVI Server</Property>
				<Property Name="TgtF_legalCopyright" Type="Str">Copyright (c) 2026 Jan Goebel, MIT license</Property>
				<Property Name="TgtF_productName" Type="Str">RemoteVI Server</Property>
				<Property Name="TgtF_targetfileGUID" Type="Str">{F15587D4-EE77-525D-B473-1B80DFE6C168}</Property>
				<Property Name="TgtF_targetfileName" Type="Str">RemoteVI Server.exe</Property>
				<Property Name="TgtF_versionIndependent" Type="Bool">false</Property>
			</Item>
			<Item Name="RemoteVI Demo" Type="EXE">
				<Property Name="App_copyErrors" Type="Bool">true</Property>
				<Property Name="App_INI_aliasGUID" Type="Str">{5DD12C81-83D5-56D5-8E69-438E666F10A4}</Property>
				<Property Name="App_INI_GUID" Type="Str">{C763F7CC-326D-5643-BDD1-FF48D3A80D44}</Property>
				<Property Name="App_serverConfig.httpPort" Type="Int">8002</Property>
				<Property Name="App_serverType" Type="Int">0</Property>
				<Property Name="Bld_autoIncrement" Type="Bool">false</Property>
				<Property Name="Bld_buildCacheID" Type="Str">{057D602E-E088-5D6F-92BB-5B039F1D0892}</Property>
				<Property Name="Bld_buildSpecName" Type="Str">RemoteVI Demo</Property>
				<Property Name="Bld_excludeInlineSubVIs" Type="Bool">true</Property>
				<Property Name="Bld_excludeLibraryItems" Type="Bool">false</Property>
				<Property Name="Bld_excludePolymorphicVIs" Type="Bool">true</Property>
				<Property Name="Bld_localDestDir" Type="Path">../builds/RemoteVI Demo</Property>
				<Property Name="Bld_localDestDirType" Type="Str">relativeToProject</Property>
				<Property Name="Bld_modifyLibraryFile" Type="Bool">true</Property>
				<Property Name="Bld_previewCacheID" Type="Str">{DE0FC532-516D-5E78-89CC-6C82045F59C4}</Property>
				<Property Name="Bld_version.build" Type="Int">0</Property>
				<Property Name="Bld_version.major" Type="Int">1</Property>
				<Property Name="Destination[0].destName" Type="Str">RemoteVI Demo.exe</Property>
				<Property Name="Destination[0].path" Type="Path">../builds/RemoteVI Demo/RemoteVI Demo.exe</Property>
				<Property Name="Destination[0].path.type" Type="Str">relativeToProject</Property>
				<Property Name="Destination[0].preserveHierarchy" Type="Bool">true</Property>
				<Property Name="Destination[0].type" Type="Str">App</Property>
				<Property Name="Destination[1].destName" Type="Str">Support Directory</Property>
				<Property Name="Destination[1].path" Type="Path">../builds/RemoteVI Demo/data</Property>
				<Property Name="Destination[1].path.type" Type="Str">relativeToProject</Property>
				<Property Name="DestinationCount" Type="Int">2</Property>
				<Property Name="Source[0].itemID" Type="Str">{BEA47062-43A9-5533-93FF-8FB5389F6067}</Property>
				<Property Name="Source[0].type" Type="Str">Container</Property>
				<Property Name="Source[1].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[1].itemID" Type="Ref">/My Computer/Examples/RemoteVI Demo.vi</Property>
				<Property Name="Source[1].sourceInclusion" Type="Str">TopLevel</Property>
				<Property Name="Source[1].type" Type="Str">VI</Property>
				<Property Name="Source[2].Library.allowMissingMembers" Type="Bool">true</Property>
				<Property Name="Source[2].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[2].itemID" Type="Ref">/My Computer/RemoteVI.lvlib</Property>
				<Property Name="Source[2].sourceInclusion" Type="Str">Include</Property>
				<Property Name="Source[2].type" Type="Str">Library</Property>
				<Property Name="Source[3].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[3].itemID" Type="Ref">/My Computer/RemoteVI.lvlib/Server/RemoteVI Server Loop.vi</Property>
				<Property Name="Source[3].sourceInclusion" Type="Str">Include</Property>
				<Property Name="Source[3].type" Type="Str">VI</Property>
				<Property Name="Source[4].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[4].itemID" Type="Ref">/My Computer/RemoteVI.lvlib/App/RemoteVI Landing Server.vi</Property>
				<Property Name="Source[4].sourceInclusion" Type="Str">Include</Property>
				<Property Name="Source[4].type" Type="Str">VI</Property>
				<Property Name="Source[5].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[5].itemID" Type="Ref">/My Computer/RemoteVI.lvlib/API/RemoteVI Status Panel.vi</Property>
				<Property Name="Source[5].sourceInclusion" Type="Str">Include</Property>
				<Property Name="Source[5].type" Type="Str">VI</Property>
				<Property Name="SourceCount" Type="Int">6</Property>
				<Property Name="TgtF_companyName" Type="Str">Jan Goebel</Property>
				<Property Name="TgtF_enableDebugging" Type="Bool">false</Property>
				<Property Name="TgtF_fileDescription" Type="Str">RemoteVI Demo - a built application that shares its own panel</Property>
				<Property Name="TgtF_internalName" Type="Str">RemoteVI Demo</Property>
				<Property Name="TgtF_legalCopyright" Type="Str">Copyright (c) 2026 Jan Goebel, MIT license</Property>
				<Property Name="TgtF_productName" Type="Str">RemoteVI Demo</Property>
				<Property Name="TgtF_targetfileGUID" Type="Str">{992BA1BE-8F8C-58E6-A301-34B4CFA9F152}</Property>
				<Property Name="TgtF_targetfileName" Type="Str">RemoteVI Demo.exe</Property>
				<Property Name="TgtF_versionIndependent" Type="Bool">false</Property>
			</Item>
		</Item>
	</Item>
</Project>
