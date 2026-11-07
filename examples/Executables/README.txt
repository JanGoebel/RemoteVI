RemoteVI example executables
============================

Three applications built with LabVIEW 2020 (64-bit). They need the LabVIEW 2020 Run-Time Engine
(64-bit), which LabVIEW 2020 installs and which is available from ni.com for other machines.

RemoteVI Demo\RemoteVI Demo.exe
    The example VI RemoteVI Demo.vi as a built application. It shares its own front panel with
    RemoteVI Start.vi on port 8088, this computer only. The link (with its access token) is shown
    on the panel; open it in a browser.

RemoteVI Application Example\RemoteVI Application Example.exe
    The example VI RemoteVI Application Example.vi as a built application: a menu on the left
    (split off by a splitter bar) loads the screens Live Data, Log Files, Alarms and Settings into
    a subpanel. It shares its own window on port 8087, this computer only; the link is shown in
    its toolbar. The data are simulated.

RemoteVI Server\RemoteVI Server.exe
    Shares any window in a browser. Pick a window on the left (LabVIEW's own first, then
    LabVIEW-built applications, then other programs), choose port, whole network and view only,
    press "Share selected window". A landing page links every share (port 8088, or the next free
    port). Closing the window stops every share.

    Command line, after "--":
      --share "<window title>"   share that window at start
      --port <n>                 port of that share (default 8100)
      --whole-network            reachable from other computers (default: this computer only)
      --view-only                the browser only watches; input is ignored
      --token <text>             a fixed access token instead of a random one
      --landing-port <n>         port of the landing page; 0 runs none

The batch files start them with different options:

    1 Demo - share its own panel.bat
    2 Server - pick a window.bat
    3 Server - share the demo, view only.bat          (port 8100)
    4 Server - share the demo with the network.bat    (port 8101, asks first)
    5 Server - share the demo, no landing page.bat    (port 8102)
    6 Application Example - share its own window.bat  (port 8087)

RemoteVI Server runs once: close it before starting it with other options.

Security: everyone who has a share's link can operate the shared window. Give it only to who
should, and share with the whole network only on a trusted network (the link travels as plain
HTTP). A window of another LabVIEW-built application is shared through Win32 (picture, clicks,
keys, menus, dialogs); Shift/Ctrl/Alt, tip strips and splitter dragging additionally need VI Server
in that application - see the RemoteVI README ("Full features for a LabVIEW-built application")
and its security notes before enabling it.
