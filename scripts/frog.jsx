$.level = 1;
var JSON;
if (!JSON) {
    JSON = {};
}
(function () {
    'use strict';
    function f(n) {
        return n < 10 ? '0' + n : n;
    }
    if (typeof Date.prototype.toJSON !== 'function') {
        Date.prototype.toJSON = function (key) {
            return isFinite(this.valueOf())
                ? this.getUTCFullYear()     + '-' +
                    f(this.getUTCMonth() + 1) + '-' +
                    f(this.getUTCDate())      + 'T' +
                    f(this.getUTCHours())     + ':' +
                    f(this.getUTCMinutes())   + ':' +
                    f(this.getUTCSeconds())   + 'Z'
                : null;
        };
        String.prototype.toJSON      =
            Number.prototype.toJSON  =
            Boolean.prototype.toJSON = function (key) {
                return this.valueOf();
            };
    }
    var cx = /[\u0000\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
        escapable = /[\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
        gap,
        indent,
        meta = {    // table of character substitutions
            '\b': '\\b',
            '\t': '\\t',
            '\n': '\\n',
            '\f': '\\f',
            '\r': '\\r',
            '"' : '\\"',
            '\\': '\\\\'
        },
        rep;
    function quote(string) {
        escapable.lastIndex = 0;
        return escapable.test(string) ? '"' + string.replace(escapable, function (a) {
            var c = meta[a];
            return typeof c === 'string'
                ? c
                : '\\u' + ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
        }) + '"' : '"' + string + '"';
    }
    function str(key, holder) {
        var i,          // The loop counter.
            k,          // The member key.
            v,          // The member value.
            length,
            mind = gap,
            partial,
            value = holder[key];
        if (value && typeof value === 'object' &&
                typeof value.toJSON === 'function') {
            value = value.toJSON(key);
        }
        if (typeof rep === 'function') {
            value = rep.call(holder, key, value);
        }
        switch (typeof value) {
        case 'string':
            return quote(value);
        case 'number':
            return isFinite(value) ? String(value) : 'null';
        case 'boolean':
        case 'null':
            return String(value);
        case 'object':
            if (!value) {
                return 'null';
            }
            gap += indent;
            partial = [];
            if (Object.prototype.toString.apply(value) === '[object Array]') {
                length = value.length;
                for (i = 0; i < length; i += 1) {
                    partial[i] = str(i, value) || 'null';
                }
                v = partial.length === 0
                    ? '[]'
                    : gap
                    ? '[\n' + gap + partial.join(',\n' + gap) + '\n' + mind + ']'
                    : '[' + partial.join(',') + ']';
                gap = mind;
                return v;
            }
            if (rep && typeof rep === 'object') {
                length = rep.length;
                for (i = 0; i < length; i += 1) {
                    if (typeof rep[i] === 'string') {
                        k = rep[i];
                        v = str(k, value);
                        if (v) {
                            partial.push(quote(k) + (gap ? ': ' : ':') + v);
                        }
                    }
                }
            } else {
                for (k in value) {
                    if (Object.prototype.hasOwnProperty.call(value, k)) {
                        v = str(k, value);
                        if (v) {
                            partial.push(quote(k) + (gap ? ': ' : ':') + v);
                        }
                    }
                }
            }
            v = partial.length === 0
                ? '{}'
                : gap
                ? '{\n' + gap + partial.join(',\n' + gap) + '\n' + mind + '}'
                : '{' + partial.join(',') + '}';
            gap = mind;
            return v;
        }
    }
    if (typeof JSON.stringify !== 'function') {
        JSON.stringify = function (value, replacer, space) {
            var i;
            gap = '';
            indent = '';
            if (typeof space === 'number') {
                for (i = 0; i < space; i += 1) {
                    indent += ' ';
                }
            } else if (typeof space === 'string') {
                indent = space;
            }
            rep = replacer;
            if (replacer && typeof replacer !== 'function' &&
                    (typeof replacer !== 'object' ||
                    typeof replacer.length !== 'number')) {
                throw new Error('JSON.stringify');
            }
            return str('', {'': value});
        };
    }
    if (typeof JSON.parse !== 'function') {
        JSON.parse = function (text, reviver) {
            var j;
            function walk(holder, key) {
                var k, v, value = holder[key];
                if (value && typeof value === 'object') {
                    for (k in value) {
                        if (Object.prototype.hasOwnProperty.call(value, k)) {
                            v = walk(value, k);
                            if (v !== undefined) {
                                value[k] = v;
                            } else {
                                delete value[k];
                            }
                        }
                    }
                }
                return reviver.call(holder, key, value);
            }
            text = String(text);
            cx.lastIndex = 0;
            if (cx.test(text)) {
                text = text.replace(cx, function (a) {
                    return '\\u' +
                        ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
                });
            }
            if (/^[\],:{}\s]*$/
                    .test(text.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g, '@')
                        .replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, ']')
                        .replace(/(?:^|:|,)(?:\s*\[)+/g, ''))) {
                j = eval('(' + text + ')');
                return typeof reviver === 'function'
                    ? walk({'': j}, '')
                    : j;
            }
            throw new SyntaxError('JSON.parse');
        };
    }
}());
(function(url) {

    // ProgressBar from Mike Hale
    function createProgressWindow(title, message, min, max, parent, useCancel) { 
       var win = new Window('palette', title); 
       win.bar = win.add('progressbar', undefined, min, max); 
       win.bar.preferredSize = [300, 20]; 
       win.stProgress = win.add('statictext');
       win.stProgress.preferredSize.width = 200;
       win.parent = undefined; 

       if (parent) { 
          if (parent instanceof Window) { 
             win.parent = parent; 
          } else if (useCancel == undefined) { 
             useCancel = parent; 
          } 
       } 

       if (useCancel) { 
          win.cancel = win.add('button', undefined, 'Cancel'); 
          win.cancel.onClick = function() { 
          try { 
             if (win.onCancel) { 
                var rc = win.onCancel(); 
                if (rc || rc == undefined) { 
                   win.close(); 
                } 
             } else { 
                win.close(); 
             } 
             } catch (e) { alert(e); } 
          } 
       }

       win.setText = function(text) {
        win.stProgress.text = text;
        win.update();
       }

       win.updateProgress = function(val) {
          var win = this;
          if (val != undefined) {
             win.bar.value = val;
          }else {
             win.bar.value++;
          }
          if (win.recenter) {
             win.center(win.parentWin);
          }
          win.update();
       }
       win.center(win.parent); 
       return win; 
    };

    var POST, pbar;
    var CONTENT = '';
    var PNG = new PNGSaveOptions();
    var pos = 0;
    var doc = app.activeDocument.fullName.fsName
    var src = new File('~/' + app.activeDocument.name);
    var socket = new Socket();
    var boundary = '------------------------------' + Date.now();
    var ext = doc.substr(doc.length - 4).toLowerCase();
    var files = [];
    var mimetypes = {
        '.png': 'image/png',
        '.jpg': 'image/jpg',
        '.gif': 'image/gif',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff',
        '.psd': 'application/octet-stream'
    };

    socket.tiemout = 20;

    pbar = createProgressWindow('Frog', 'Saving Files', 0, 100, false, true);
    pbar.show();
    pbar.isDone = false;
    
    if (ext !== '.png') {
        var opt;
        switch(ext) {
            case '.jpg':
                opt = new JPEGSaveOptions();
                break;
            case '.gif':
                opt = new GIFSaveOptions();
                break;
            case '.tif':
            case '.tiff':
                opt = new TiffSaveOptions();
                break;
            case '.psd':
                opt = new PhotoshopSaveOptions();
                break;
        }
        var png = new File(src.fsName.substr(0, src.fsName.length - 4) + '.png');
        app.activeDocument.saveAs(src, opt, true);
        pbar.setText('Saving ' + src.name);
        pbar.updateProgress();
        app.activeDocument.saveAs(png, PNG, true);
        pbar.setText('Saving ' + png.name);
        pbar.updateProgress();
        files.push(['file', png]);
        files.push([src.name, src]);
    }
    else {
        app.activeDocument.saveAs(src, PNG, true);
        pbar.setText('Saving ' + src.name);
        pbar.updateProgress();
        files.push(['file', src]);
    }

    for (var i=0;i<files.length;i++) {
        var name = files[i][0];
        var file = files[i][1];
        var ext = file.fsName.substr(file.fsName.length - 4).toLowerCase();
        var mime = mimetypes[ext];
        file.open('r');
        file.encoding = 'BINARY';
        data = file.read();
        file.close();
    
        CONTENT += '--' + boundary + '\n';
        CONTENT += 'Content-Disposition: form-data; name="' + name + '"; filename="' + file.name + '"\r\n';
        CONTENT += 'Content-Type: ' + mime + '\r\n\r\n';
        CONTENT += data + '\n';
        CONTENT += '--' + boundary + '--';
    }
    
    POST = 'POST ' + url + ' HTTP/1.1\n';
    POST += 'User-Agent: Photoshop\n';
    POST += 'Host: 127.0.0.1\n';
    POST += 'Content-length: ' + CONTENT.length + '\n';
    POST += 'Content-Type: multipart/form-data; boundary=' + boundary + '\r\n\r\n';
    POST += CONTENT;
    
    socket.open('127.0.0.1:8080', 'binary');
    
    pbar.bar.maxvalue = POST.length / 1024;
    pbar.setText('Sending image...');
    
    while (pos < POST.length) {
        socket.write(POST.substr(pos, 1024));
        pos += 1024;
        pbar.updateProgress();
    }
    pbar.isDone = true;
    pbar.close();
    socket.write(POST);
    POST = '';
    var x = '';
    while (!socket.eof) {
        x += socket.read(1024);
    }

    socket.close();
    
    if (x) {
        var res = JSON.parse(x.split('\r\n\r\n')[1]);
    }
    
    for (var i=0;i<files.length;i++) {
        var file = files[i][1];
        file.remove();
    }
    
    if (res.isError) {
        alert(res.message);
    }
    else if (res.message !== '') {
        alert(res.message);
    }
    else {
        alert('Success');
    }
})('/');