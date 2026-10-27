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
				<Item Name="BitBlt Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/BitBlt Wrapper Template.vi"/>
				<Item Name="ChildWindowFromPointEx Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/ChildWindowFromPointEx Wrapper Template.vi"/>
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
				<Item Name="IsWindowEnabled Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/IsWindowEnabled Wrapper Template.vi"/>
				<Item Name="IsWindowVisible Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/IsWindowVisible Wrapper Template.vi"/>
				<Item Name="PostMessageW Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/PostMessageW Wrapper Template.vi"/>
				<Item Name="PrintWindow Wrapper Template.vi" Type="VI" URL="../scripts/Win32 Wrapper Templates/PrintWindow Wrapper Template.vi"/>
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
					<Item Name="RemoteVI Check Frame Encode.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Frame Encode.vi"/>
					<Item Name="RemoteVI Check Overlay Encode.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Overlay Encode.vi"/>
					<Item Name="RemoteVI Check Parse Input.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Parse Input.vi"/>
					<Item Name="RemoteVI Check Track Modifiers.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Track Modifiers.vi"/>
					<Item Name="RemoteVI Check Translate Input.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Translate Input.vi"/>
					<Item Name="RemoteVI Check Window Frame Encode.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check Window Frame Encode.vi"/>
					<Item Name="RemoteVI Check WS Decode Client Frame.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check WS Decode Client Frame.vi"/>
					<Item Name="RemoteVI Check WS Encode Server Frame.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Check WS Encode Server Frame.vi"/>
					<Item Name="RemoteVI Test Bytes To Hex.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Test Bytes To Hex.vi"/>
					<Item Name="RemoteVI Test Hex To Bytes.vi" Type="VI" URL="../tests/caraya/support/RemoteVI Test Hex To Bytes.vi"/>
				</Item>
				<Item Name="unit" Type="Folder">
					<Item Name="Capture" Type="Folder">
						<Item Name="Test Dirty Rects.vi" Type="VI" URL="../tests/caraya/unit/Capture/Test Dirty Rects.vi"/>
					</Item>
					<Item Name="Input" Type="Folder">
						<Item Name="Test Track Modifiers.vi" Type="VI" URL="../tests/caraya/unit/Input/Test Track Modifiers.vi"/>
						<Item Name="Test Translate Input.vi" Type="VI" URL="../tests/caraya/unit/Input/Test Translate Input.vi"/>
					</Item>
					<Item Name="Protocol" Type="Folder">
						<Item Name="Test Frame Encode.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test Frame Encode.vi"/>
						<Item Name="Test Overlay Encode.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test Overlay Encode.vi"/>
						<Item Name="Test Parse Input.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test Parse Input.vi"/>
						<Item Name="Test Window Frame Encode.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test Window Frame Encode.vi"/>
						<Item Name="Test WS Decode Client Frame.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test WS Decode Client Frame.vi"/>
						<Item Name="Test WS Encode Server Frame.vi" Type="VI" URL="../tests/caraya/unit/Protocol/Test WS Encode Server Frame.vi"/>
					</Item>
				</Item>
				<Item Name="RemoteVI Caraya Runner.vi" Type="VI" URL="../tests/caraya/RemoteVI Caraya Runner.vi"/>
			</Item>
			<Item Name="Fixture" Type="Folder">
				<Item Name="build" Type="Folder">
					<Item Name="Fixture Tab Panel.vi" Type="VI" URL="../tests/fixtures/build/Fixture Tab Panel.vi"/>
				</Item>
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
		<Item Name="Dependencies" Type="Dependencies"/>
		<Item Name="Build Specifications" Type="Build"/>
	</Item>
</Project>
