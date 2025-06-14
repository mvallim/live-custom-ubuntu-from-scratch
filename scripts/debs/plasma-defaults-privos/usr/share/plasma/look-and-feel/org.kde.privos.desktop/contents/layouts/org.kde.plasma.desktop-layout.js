loadTemplate("org.kde.plasma.desktop.defaultPanel")

var allDesktops = desktops();

for (var i = 0; i < allDesktops.length; i++) {
    var desktop = allDesktops[i];

    desktop.wallpaperPlugin = "org.kde.image";
    desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desktop.writeConfig("Image", "file:///usr/share/backgrounds/privos.jpg");
}
