function saveWebImage(filename) {
    var file = new File(filename);
    var dot = file.name.lastIndexOf('.');
    var namebase = file.name.slice(0, dot);
    var dest = new File($.getenv('TEMP') + '\\frog_temp\\' + namebase + '.png');

    if (!dest.parent.exists) {
        dest.parent.create();
    }

    app.activeDocument.saveAs(dest, PNGSaveOptions, true);

    return dest.fsName;
}
