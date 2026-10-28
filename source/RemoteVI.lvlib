<?xml version='1.0' encoding='UTF-8'?>
<Library LVVersion="25008000">
	<Property Name="NI.Lib.Description" Type="Str">RemoteVI - publish a LabVIEW front panel to a web browser, pixel-accurate and interactive.

Public API: use API/RemoteVI Start.vi to publish a VI's front panel and API/RemoteVI Stop.vi to stop publishing it. Everything else (Server, Capture, Protocol, Input, Win32) is internal implementation; it is public only so the tests, fixtures and benchmarks can call it directly, and it may change without notice.</Property>
	<Property Name="NI.Lib.Icon" Type="Bin">*1#!!!!!!!)!"1!&amp;!!!-!%!!!@````]!!!!"!!%!!!)]!!!*Q(C=\:3R51."$%5`$!'J9R,',;A&amp;N_!7V))$%I&gt;O12GR7\A'#.4#T:!T=S8Y?,=HQ!-'*T!1M'O&gt;VV^;[&gt;XO?K87LK5LD?@;QZ@NR4`FYTG.WFDP`&lt;0H&gt;@2B`DH`5@\4]Y^^*`/`F@CU@NE*`M`@8V_W@`_``X@^:RIRW\."0^SECU;+*2;99^&lt;?&lt;ETU2%`U2%`U2!`U1!`U1!`U1(&gt;U2X&gt;U2X&gt;U2T&gt;U1T&gt;U1T&gt;U1W]&gt;8?B#&amp;TKLEB20#C6*EQ2*-#B+(AF0QJ0Q*$T]6-+4]#1]#5`#1YA3HI1HY5FY%B[G+?&amp;*?"+?B#@B)65DS&gt;&lt;2Y5FY3+_!*_!*?!+?A)?3#HA#A+"9E$B)!I9#:T!)?!+?A)?B!J[!*_!*?!)?X!JY!J[!*_!*?*D36C5;T&gt;42Y3'.("[(R_&amp;R?"Q?5MPB=8A=(I@(Y;'=("[(RY&amp;Q#DL*1:!TS1FQ@DA]$A^@=HA=(I@(Y8&amp;Y=,5&gt;]L9S%]X5U?%R?!Q?A]@A-8B))90(Y$&amp;Y$"[$B\1S?!Q?A]@A-8AI*90(Y$&amp;Y$"#D+/6F*$-G'E''90$Q;;@&amp;WCZ&amp;)\(7[[]Z(V46!61&gt;,.7"52U%V1;L.E[V);K&amp;6CWA;G&amp;5,[R[%27AKL!KI3J1!]]?[\!^NM-WW"J&lt;95NM-5X^ZM"B'.4XP&lt;KOUX[`VW[XUW;TU8K^VGKVUH+ZV'+R?,WN&lt;OFTOTC_FQYX^_0BK:PN"OOQ`GY]$)`.PS8_OWW_F`\#X;B,D5@80'PU$-W\Q59!!!!!</Property>
	<Property Name="NI.Lib.SourceVersion" Type="Int">620789760</Property>
	<Property Name="NI.Lib.Version" Type="Str">1.0.0.0</Property>
	<Property Name="NI.LV.All.SourceOnly" Type="Bool">true</Property>
	<Item Name="API" Type="Folder">
		<Item Name="RemoteVI Start.vi" Type="VI" URL="../API/RemoteVI Start.vi"/>
		<Item Name="RemoteVI Status.vi" Type="VI" URL="../API/RemoteVI Status.vi"/>
		<Item Name="RemoteVI Stop.vi" Type="VI" URL="../API/RemoteVI Stop.vi"/>
	</Item>
	<Item Name="Capture" Type="Folder">
		<Item Name="RemoteVI Capture Panel.vi" Type="VI" URL="../Capture/RemoteVI Capture Panel.vi"/>
		<Item Name="RemoteVI Dirty Band.vi" Type="VI" URL="../Capture/RemoteVI Dirty Band.vi"/>
		<Item Name="RemoteVI Dirty Rects.vi" Type="VI" URL="../Capture/RemoteVI Dirty Rects.vi"/>
		<Item Name="RemoteVI Encode Rect PNG.vi" Type="VI" URL="../Capture/RemoteVI Encode Rect PNG.vi"/>
	</Item>
	<Item Name="Input" Type="Folder">
		<Item Name="RemoteVI Apply Modifiers.vi" Type="VI" URL="../Input/RemoteVI Apply Modifiers.vi"/>
		<Item Name="RemoteVI Cancel Popups.vi" Type="VI" URL="../Input/RemoteVI Cancel Popups.vi"/>
		<Item Name="RemoteVI Close Submenus.vi" Type="VI" URL="../Input/RemoteVI Close Submenus.vi"/>
		<Item Name="RemoteVI Close Window.vi" Type="VI" URL="../Input/RemoteVI Close Window.vi"/>
		<Item Name="RemoteVI Get Panel Geometry.vi" Type="VI" URL="../Input/RemoteVI Get Panel Geometry.vi"/>
		<Item Name="RemoteVI Highlight Menu Row.vi" Type="VI" URL="../Input/RemoteVI Highlight Menu Row.vi"/>
		<Item Name="RemoteVI Hover Decision.vi" Type="VI" URL="../Input/RemoteVI Hover Decision.vi"/>
		<Item Name="RemoteVI Hover Menus.vi" Type="VI" URL="../Input/RemoteVI Hover Menus.vi"/>
		<Item Name="RemoteVI Hover Navigate.vi" Type="VI" URL="../Input/RemoteVI Hover Navigate.vi"/>
		<Item Name="RemoteVI Hover Parent Menu.vi" Type="VI" URL="../Input/RemoteVI Hover Parent Menu.vi"/>
		<Item Name="RemoteVI Is Button Down.vi" Type="VI" URL="../Input/RemoteVI Is Button Down.vi"/>
		<Item Name="RemoteVI Menu Click.vi" Type="VI" URL="../Input/RemoteVI Menu Click.vi"/>
		<Item Name="RemoteVI Menu Pointer.vi" Type="VI" URL="../Input/RemoteVI Menu Pointer.vi"/>
		<Item Name="RemoteVI Note Popup Pointer.vi" Type="VI" URL="../Input/RemoteVI Note Popup Pointer.vi"/>
		<Item Name="RemoteVI Pack Point lParam.vi" Type="VI" URL="../Input/RemoteVI Pack Point lParam.vi"/>
		<Item Name="RemoteVI Plain Popup Click.vi" Type="VI" URL="../Input/RemoteVI Plain Popup Click.vi"/>
		<Item Name="RemoteVI Point On Popup.vi" Type="VI" URL="../Input/RemoteVI Point On Popup.vi"/>
		<Item Name="RemoteVI Popup Click.vi" Type="VI" URL="../Input/RemoteVI Popup Click.vi"/>
		<Item Name="RemoteVI Post At Cursor.vi" Type="VI" URL="../Input/RemoteVI Post At Cursor.vi"/>
		<Item Name="RemoteVI Post Input.vi" Type="VI" URL="../Input/RemoteVI Post Input.vi"/>
		<Item Name="RemoteVI Post Menu Key.vi" Type="VI" URL="../Input/RemoteVI Post Menu Key.vi"/>
		<Item Name="RemoteVI Route Input.vi" Type="VI" URL="../Input/RemoteVI Route Input.vi"/>
		<Item Name="RemoteVI Swallow Button Up.vi" Type="VI" URL="../Input/RemoteVI Swallow Button Up.vi"/>
		<Item Name="RemoteVI Track Modifiers.vi" Type="VI" URL="../Input/RemoteVI Track Modifiers.vi"/>
		<Item Name="RemoteVI Translate Input.vi" Type="VI" URL="../Input/RemoteVI Translate Input.vi"/>
		<Item Name="RemoteVI Wait Popup Age.vi" Type="VI" URL="../Input/RemoteVI Wait Popup Age.vi"/>
	</Item>
	<Item Name="Protocol" Type="Folder">
		<Item Name="RemoteVI Frame Encode.vi" Type="VI" URL="../Protocol/RemoteVI Frame Encode.vi"/>
		<Item Name="RemoteVI JSON String.vi" Type="VI" URL="../Protocol/RemoteVI JSON String.vi"/>
		<Item Name="RemoteVI Overlay Encode.vi" Type="VI" URL="../Protocol/RemoteVI Overlay Encode.vi"/>
		<Item Name="RemoteVI Parse Input.vi" Type="VI" URL="../Protocol/RemoteVI Parse Input.vi"/>
		<Item Name="RemoteVI Splitters Message.vi" Type="VI" URL="../Protocol/RemoteVI Splitters Message.vi"/>
		<Item Name="RemoteVI Tips Message.vi" Type="VI" URL="../Protocol/RemoteVI Tips Message.vi"/>
		<Item Name="RemoteVI Window Frame Encode.vi" Type="VI" URL="../Protocol/RemoteVI Window Frame Encode.vi"/>
		<Item Name="RemoteVI Windows Message.vi" Type="VI" URL="../Protocol/RemoteVI Windows Message.vi"/>
		<Item Name="RemoteVI WS Decode Client Frame.vi" Type="VI" URL="../Protocol/RemoteVI WS Decode Client Frame.vi"/>
		<Item Name="RemoteVI WS Encode Server Frame.vi" Type="VI" URL="../Protocol/RemoteVI WS Encode Server Frame.vi"/>
	</Item>
	<Item Name="Server" Type="Folder">
		<Item Name="RemoteVI Accept Clients.vi" Type="VI" URL="../Server/RemoteVI Accept Clients.vi"/>
		<Item Name="RemoteVI Add Client.vi" Type="VI" URL="../Server/RemoteVI Add Client.vi"/>
		<Item Name="RemoteVI Announce Listener.vi" Type="VI" URL="../Server/RemoteVI Announce Listener.vi"/>
		<Item Name="RemoteVI Answer Control Frame.vi" Type="VI" URL="../Server/RemoteVI Answer Control Frame.vi"/>
		<Item Name="RemoteVI Apply Splitter.vi" Type="VI" URL="../Server/RemoteVI Apply Splitter.vi"/>
		<Item Name="RemoteVI Capture And Send.vi" Type="VI" URL="../Server/RemoteVI Capture And Send.vi"/>
		<Item Name="RemoteVI Capture Frame.vi" Type="VI" URL="../Server/RemoteVI Capture Frame.vi"/>
		<Item Name="RemoteVI Capture Windows.vi" Type="VI" URL="../Server/RemoteVI Capture Windows.vi"/>
		<Item Name="RemoteVI Classify Client Frame.vi" Type="VI" URL="../Server/RemoteVI Classify Client Frame.vi"/>
		<Item Name="RemoteVI Click State.vi" Type="VI" URL="../Server/RemoteVI Click State.vi"/>
		<Item Name="RemoteVI Client Panel.vi" Type="VI" URL="../Server/RemoteVI Client Panel.vi"/>
		<Item Name="RemoteVI Close Clients.vi" Type="VI" URL="../Server/RemoteVI Close Clients.vi"/>
		<Item Name="RemoteVI Control Children.vi" Type="VI" URL="../Server/RemoteVI Control Children.vi"/>
		<Item Name="RemoteVI Cross Origin.vi" Type="VI" URL="../Server/RemoteVI Cross Origin.vi"/>
		<Item Name="RemoteVI Drop Closed Clients.vi" Type="VI" URL="../Server/RemoteVI Drop Closed Clients.vi"/>
		<Item Name="RemoteVI Encode Popups.vi" Type="VI" URL="../Server/RemoteVI Encode Popups.vi"/>
		<Item Name="RemoteVI Format Duration.vi" Type="VI" URL="../Server/RemoteVI Format Duration.vi"/>
		<Item Name="RemoteVI Greeting.vi" Type="VI" URL="../Server/RemoteVI Greeting.vi"/>
		<Item Name="RemoteVI Handle Connection.vi" Type="VI" URL="../Server/RemoteVI Handle Connection.vi"/>
		<Item Name="RemoteVI Handle Text Message.vi" Type="VI" URL="../Server/RemoteVI Handle Text Message.vi"/>
		<Item Name="RemoteVI Hide Remote Popups.vi" Type="VI" URL="../Server/RemoteVI Hide Remote Popups.vi"/>
		<Item Name="RemoteVI Index HTML.vi" Type="VI" URL="../Server/RemoteVI Index HTML.vi"/>
		<Item Name="RemoteVI Launch Server Loop.vi" Type="VI" URL="../Server/RemoteVI Launch Server Loop.vi"/>
		<Item Name="RemoteVI List Popups.vi" Type="VI" URL="../Server/RemoteVI List Popups.vi"/>
		<Item Name="RemoteVI Logical Popups.vi" Type="VI" URL="../Server/RemoteVI Logical Popups.vi"/>
		<Item Name="RemoteVI Loop Flags.vi" Type="VI" URL="../Server/RemoteVI Loop Flags.vi"/>
		<Item Name="RemoteVI Menu Hover.vi" Type="VI" URL="../Server/RemoteVI Menu Hover.vi"/>
		<Item Name="RemoteVI New Token.vi" Type="VI" URL="../Server/RemoteVI New Token.vi"/>
		<Item Name="RemoteVI Open Server Loop.vi" Type="VI" URL="../Server/RemoteVI Open Server Loop.vi"/>
		<Item Name="RemoteVI Origin Message.vi" Type="VI" URL="../Server/RemoteVI Origin Message.vi"/>
		<Item Name="RemoteVI Other Shares.vi" Type="VI" URL="../Server/RemoteVI Other Shares.vi"/>
		<Item Name="RemoteVI Panel Controls.vi" Type="VI" URL="../Server/RemoteVI Panel Controls.vi"/>
		<Item Name="RemoteVI Post Client Input.vi" Type="VI" URL="../Server/RemoteVI Post Client Input.vi"/>
		<Item Name="RemoteVI Publish Status.vi" Type="VI" URL="../Server/RemoteVI Publish Status.vi"/>
		<Item Name="RemoteVI Read Client Bytes.vi" Type="VI" URL="../Server/RemoteVI Read Client Bytes.vi"/>
		<Item Name="RemoteVI Read Request Head.vi" Type="VI" URL="../Server/RemoteVI Read Request Head.vi"/>
		<Item Name="RemoteVI Read Splitters.vi" Type="VI" URL="../Server/RemoteVI Read Splitters.vi"/>
		<Item Name="RemoteVI Read Tips.vi" Type="VI" URL="../Server/RemoteVI Read Tips.vi"/>
		<Item Name="RemoteVI Refresh Geometry.vi" Type="VI" URL="../Server/RemoteVI Refresh Geometry.vi"/>
		<Item Name="RemoteVI Retrack Popups.vi" Type="VI" URL="../Server/RemoteVI Retrack Popups.vi"/>
		<Item Name="RemoteVI Route Request.vi" Type="VI" URL="../Server/RemoteVI Route Request.vi"/>
		<Item Name="RemoteVI Running Panels.vi" Type="VI" URL="../Server/RemoteVI Running Panels.vi"/>
		<Item Name="RemoteVI Send Client Windows.vi" Type="VI" URL="../Server/RemoteVI Send Client Windows.vi"/>
		<Item Name="RemoteVI Send Frame.vi" Type="VI" URL="../Server/RemoteVI Send Frame.vi"/>
		<Item Name="RemoteVI Send Origin.vi" Type="VI" URL="../Server/RemoteVI Send Origin.vi"/>
		<Item Name="RemoteVI Send Overlay.vi" Type="VI" URL="../Server/RemoteVI Send Overlay.vi"/>
		<Item Name="RemoteVI Send Static Response.vi" Type="VI" URL="../Server/RemoteVI Send Static Response.vi"/>
		<Item Name="RemoteVI Send Tips.vi" Type="VI" URL="../Server/RemoteVI Send Tips.vi"/>
		<Item Name="RemoteVI Send Window Frame.vi" Type="VI" URL="../Server/RemoteVI Send Window Frame.vi"/>
		<Item Name="RemoteVI Send Windows.vi" Type="VI" URL="../Server/RemoteVI Send Windows.vi"/>
		<Item Name="RemoteVI Serve Pending Connection.vi" Type="VI" URL="../Server/RemoteVI Serve Pending Connection.vi"/>
		<Item Name="RemoteVI Server Loop.vi" Type="VI" URL="../Server/RemoteVI Server Loop.vi"/>
		<Item Name="RemoteVI Server Setup.vi" Type="VI" URL="../Server/RemoteVI Server Setup.vi"/>
		<Item Name="RemoteVI Service Client.vi" Type="VI" URL="../Server/RemoteVI Service Client.vi"/>
		<Item Name="RemoteVI Service Clients.vi" Type="VI" URL="../Server/RemoteVI Service Clients.vi"/>
		<Item Name="RemoteVI Set Server Loop Inputs.vi" Type="VI" URL="../Server/RemoteVI Set Server Loop Inputs.vi"/>
		<Item Name="RemoteVI Share Running.vi" Type="VI" URL="../Server/RemoteVI Share Running.vi"/>
		<Item Name="RemoteVI Splitter Request.vi" Type="VI" URL="../Server/RemoteVI Splitter Request.vi"/>
		<Item Name="RemoteVI Status Convert.vi" Type="VI" URL="../Server/RemoteVI Status Convert.vi"/>
		<Item Name="RemoteVI Status Registry.vi" Type="VI" URL="../Server/RemoteVI Status Registry.vi"/>
		<Item Name="RemoteVI Status Text.vi" Type="VI" URL="../Server/RemoteVI Status Text.vi"/>
		<Item Name="RemoteVI Token Check.vi" Type="VI" URL="../Server/RemoteVI Token Check.vi"/>
		<Item Name="RemoteVI Track Popups.vi" Type="VI" URL="../Server/RemoteVI Track Popups.vi"/>
		<Item Name="RemoteVI Track Windows.vi" Type="VI" URL="../Server/RemoteVI Track Windows.vi"/>
		<Item Name="RemoteVI VI Stopped.vi" Type="VI" URL="../Server/RemoteVI VI Stopped.vi"/>
		<Item Name="RemoteVI Write To Clients.vi" Type="VI" URL="../Server/RemoteVI Write To Clients.vi"/>
		<Item Name="RemoteVI Yield If Idle.vi" Type="VI" URL="../Server/RemoteVI Yield If Idle.vi"/>
	</Item>
	<Item Name="Win32" Type="Folder">
		<Item Name="bcrypt BCryptGenRandom.vi" Type="VI" URL="../Win32/bcrypt BCryptGenRandom.vi"/>
		<Item Name="gdi32 BitBlt.vi" Type="VI" URL="../Win32/gdi32 BitBlt.vi"/>
		<Item Name="gdi32 CreateCompatibleBitmap.vi" Type="VI" URL="../Win32/gdi32 CreateCompatibleBitmap.vi"/>
		<Item Name="gdi32 CreateCompatibleDC.vi" Type="VI" URL="../Win32/gdi32 CreateCompatibleDC.vi"/>
		<Item Name="gdi32 CreateRectRgn.vi" Type="VI" URL="../Win32/gdi32 CreateRectRgn.vi"/>
		<Item Name="gdi32 DeleteDC.vi" Type="VI" URL="../Win32/gdi32 DeleteDC.vi"/>
		<Item Name="gdi32 DeleteObject.vi" Type="VI" URL="../Win32/gdi32 DeleteObject.vi"/>
		<Item Name="gdi32 GetDIBits.vi" Type="VI" URL="../Win32/gdi32 GetDIBits.vi"/>
		<Item Name="gdi32 SelectObject.vi" Type="VI" URL="../Win32/gdi32 SelectObject.vi"/>
		<Item Name="kernel32 CloseHandle.vi" Type="VI" URL="../Win32/kernel32 CloseHandle.vi"/>
		<Item Name="kernel32 GetCurrentProcessId.vi" Type="VI" URL="../Win32/kernel32 GetCurrentProcessId.vi"/>
		<Item Name="kernel32 GetCurrentThreadId.vi" Type="VI" URL="../Win32/kernel32 GetCurrentThreadId.vi"/>
		<Item Name="kernel32 OpenProcess.vi" Type="VI" URL="../Win32/kernel32 OpenProcess.vi"/>
		<Item Name="kernel32 QueryFullProcessImageNameW.vi" Type="VI" URL="../Win32/kernel32 QueryFullProcessImageNameW.vi"/>
		<Item Name="RemoteVI Capture Window.vi" Type="VI" URL="../Win32/RemoteVI Capture Window.vi"/>
		<Item Name="RemoteVI Copy Window.vi" Type="VI" URL="../Win32/RemoteVI Copy Window.vi"/>
		<Item Name="RemoteVI Cursor Outside Window.vi" Type="VI" URL="../Win32/RemoteVI Cursor Outside Window.vi"/>
		<Item Name="RemoteVI Find Popups.vi" Type="VI" URL="../Win32/RemoteVI Find Popups.vi"/>
		<Item Name="RemoteVI Frame Rect.vi" Type="VI" URL="../Win32/RemoteVI Frame Rect.vi"/>
		<Item Name="RemoteVI Hide Window.vi" Type="VI" URL="../Win32/RemoteVI Hide Window.vi"/>
		<Item Name="RemoteVI List Menus.vi" Type="VI" URL="../Win32/RemoteVI List Menus.vi"/>
		<Item Name="RemoteVI List Windows.vi" Type="VI" URL="../Win32/RemoteVI List Windows.vi"/>
		<Item Name="RemoteVI Menu Highlight.vi" Type="VI" URL="../Win32/RemoteVI Menu Highlight.vi"/>
		<Item Name="RemoteVI Mouse Captured.vi" Type="VI" URL="../Win32/RemoteVI Mouse Captured.vi"/>
		<Item Name="RemoteVI Restore If Minimized.vi" Type="VI" URL="../Win32/RemoteVI Restore If Minimized.vi"/>
		<Item Name="RemoteVI Set Modifier Keys.vi" Type="VI" URL="../Win32/RemoteVI Set Modifier Keys.vi"/>
		<Item Name="RemoteVI System Color.vi" Type="VI" URL="../Win32/RemoteVI System Color.vi"/>
		<Item Name="RemoteVI Thread Windows.vi" Type="VI" URL="../Win32/RemoteVI Thread Windows.vi"/>
		<Item Name="RemoteVI Wait Highlight Change.vi" Type="VI" URL="../Win32/RemoteVI Wait Highlight Change.vi"/>
		<Item Name="RemoteVI Wait Input Handled.vi" Type="VI" URL="../Win32/RemoteVI Wait Input Handled.vi"/>
		<Item Name="RemoteVI Window Info.vi" Type="VI" URL="../Win32/RemoteVI Window Info.vi"/>
		<Item Name="RemoteVI Window Popup Info.vi" Type="VI" URL="../Win32/RemoteVI Window Popup Info.vi"/>
		<Item Name="user32 AttachThreadInput.vi" Type="VI" URL="../Win32/user32 AttachThreadInput.vi"/>
		<Item Name="user32 ChildWindowFromPointEx.vi" Type="VI" URL="../Win32/user32 ChildWindowFromPointEx.vi"/>
		<Item Name="user32 FindWindowExW.vi" Type="VI" URL="../Win32/user32 FindWindowExW.vi"/>
		<Item Name="user32 GetAncestor.vi" Type="VI" URL="../Win32/user32 GetAncestor.vi"/>
		<Item Name="user32 GetClassNameW.vi" Type="VI" URL="../Win32/user32 GetClassNameW.vi"/>
		<Item Name="user32 GetClientRect.vi" Type="VI" URL="../Win32/user32 GetClientRect.vi"/>
		<Item Name="user32 GetCursorPos.vi" Type="VI" URL="../Win32/user32 GetCursorPos.vi"/>
		<Item Name="user32 GetDC.vi" Type="VI" URL="../Win32/user32 GetDC.vi"/>
		<Item Name="user32 GetGUIThreadInfo.vi" Type="VI" URL="../Win32/user32 GetGUIThreadInfo.vi"/>
		<Item Name="user32 GetKeyboardState.vi" Type="VI" URL="../Win32/user32 GetKeyboardState.vi"/>
		<Item Name="user32 GetSysColor.vi" Type="VI" URL="../Win32/user32 GetSysColor.vi"/>
		<Item Name="user32 GetWindow.vi" Type="VI" URL="../Win32/user32 GetWindow.vi"/>
		<Item Name="user32 GetWindowLongPtrW.vi" Type="VI" URL="../Win32/user32 GetWindowLongPtrW.vi"/>
		<Item Name="user32 GetWindowRect.vi" Type="VI" URL="../Win32/user32 GetWindowRect.vi"/>
		<Item Name="user32 GetWindowTextW.vi" Type="VI" URL="../Win32/user32 GetWindowTextW.vi"/>
		<Item Name="user32 GetWindowThreadProcessId.vi" Type="VI" URL="../Win32/user32 GetWindowThreadProcessId.vi"/>
		<Item Name="user32 IsIconic.vi" Type="VI" URL="../Win32/user32 IsIconic.vi"/>
		<Item Name="user32 IsWindow.vi" Type="VI" URL="../Win32/user32 IsWindow.vi"/>
		<Item Name="user32 IsWindowEnabled.vi" Type="VI" URL="../Win32/user32 IsWindowEnabled.vi"/>
		<Item Name="user32 IsWindowVisible.vi" Type="VI" URL="../Win32/user32 IsWindowVisible.vi"/>
		<Item Name="user32 PostMessageW.vi" Type="VI" URL="../Win32/user32 PostMessageW.vi"/>
		<Item Name="user32 PrintWindow.vi" Type="VI" URL="../Win32/user32 PrintWindow.vi"/>
		<Item Name="user32 ReleaseDC.vi" Type="VI" URL="../Win32/user32 ReleaseDC.vi"/>
		<Item Name="user32 ScreenToClient.vi" Type="VI" URL="../Win32/user32 ScreenToClient.vi"/>
		<Item Name="user32 SendMessageTimeoutW.vi" Type="VI" URL="../Win32/user32 SendMessageTimeoutW.vi"/>
		<Item Name="user32 SetKeyboardState.vi" Type="VI" URL="../Win32/user32 SetKeyboardState.vi"/>
		<Item Name="user32 SetLayeredWindowAttributes.vi" Type="VI" URL="../Win32/user32 SetLayeredWindowAttributes.vi"/>
		<Item Name="user32 SetWindowLongPtrW.vi" Type="VI" URL="../Win32/user32 SetWindowLongPtrW.vi"/>
		<Item Name="user32 SetWindowPos.vi" Type="VI" URL="../Win32/user32 SetWindowPos.vi"/>
		<Item Name="user32 SetWindowRgn.vi" Type="VI" URL="../Win32/user32 SetWindowRgn.vi"/>
		<Item Name="user32 ShowWindow.vi" Type="VI" URL="../Win32/user32 ShowWindow.vi"/>
	</Item>
</Library>
