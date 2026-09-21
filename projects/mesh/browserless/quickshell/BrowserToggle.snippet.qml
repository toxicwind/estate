// BrowserToggle.snippet.qml - canonical record of the keeper-browser toggle
// button installed into the Quickshell bar.
//
// INSTALL: this Loader block is appended inside the RowLayout of
//   ~/.config/quickshell/ii/modules/ii/bar/UtilButtons.qml
// It renders a CircleUtilButton (matching the other util buttons) that runs
// keeper/browser-toggle.sh to show/hide the keeper Chromium window via the
// Hyprland scratchpad. Quickshell picks up the config change live.
        Loader {
            active: true
            visible: true
            sourceComponent: CircleUtilButton {
                Layout.alignment: Qt.AlignVCenter
                toolTipText: Translation.tr("Show/hide keeper browser")
                onClicked: {
                    Quickshell.execDetached(["/home/toxic/sovereign/projects/mesh/browserless/keeper/browser-toggle.sh"]);
                }
                MaterialSymbol {
                    horizontalAlignment: Qt.AlignHCenter
                    fill: 1
                    text: "web"
                    iconSize: Appearance.font.pixelSize.large
                    color: Appearance.colors.colOnLayer2
                }
            }
        }
