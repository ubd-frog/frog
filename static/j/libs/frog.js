/*

Frog Classes

- Gallery
- Piece
    - Image
    - Video
- Viewer
    -Video Controls (use other?)
- Thumbnail
- Marquee

Which UI to use?

*/

(function(global) {
    var Frog = {};
    if (typeof exports !== 'undefined') {
        if (typeof module !== 'undefined') {
            module.exports = Frog;
        }
        else {
            exports = Frog;
        }
    }
    else {
        global.Frog = Frog;
    }

    Frog.pixel = null;
    Frog.getPixel = function() {
        if (Frog.pixel === null) {
            var canvas = document.createElement('canvas');
            var ctx = canvas.getContext('2d');
            canvas.width = 1;
            canvas.height = 1;

            ctx.fillStyle = 'rgba(0,0,0,0)';
            ctx.fillRect(0,0,1,1);
            Frog.pixel = 'data:image/png;base64,' + canvas.toDataURL('image/png','').substring(22);
        }

        return Frog.pixel;
    }
    Frog.util = {
        fitToRect: function(rectW, rectH, width, height) {
            var iratio = width / height;
            var wratio = rectW / rectH;
            var scale;

            if (iratio > wratio) {
                scale = rectW / width;
            }
            else {
                scale = rectH / height;
            }

            return {width: width * scale, height: height * scale};
        }
    }
    Frog.TagManager = new Class({
        initialize: function() {
            this.tags = {};
            var self = this;
            new Request.JSON({
                url: '/frog/tag/',
                onSuccess: function(res) {
                    if (res.isSuccess) {
                        res.values.each(function(tag) {
                            self.tags[tag.id] = tag.name;
                        });
                    }
                    else if (res.isError) {
                        throw res.message;
                    }
                }
            }).GET({json:true});
        },
        get: function(arg) {
            var value;
            var self = this;
            if (typeOf(arg) === 'number') {
                value = this.tags[arg];
            }
            else {
                var idx = Object.values(this.tags).indexOf(arg);
                if (idx >= 0) {
                    value = Object.keys(this.tags)[idx];
                }
                else {
                    new Request.JSON({
                        url: '/frog/tag/',
                        async: false,
                        onSuccess: function(res) {
                            if (res.isSuccess) {
                                value = res.value.id;
                                self.tags[value] = res.value.name;
                            }
                        }
                    }).POST({name: arg});
                }
            }
            
            return value;
        },
        getByName: function(name) {

        },
        getByID: function(id) {

        }
    });
    Frog.Tags = new Frog.TagManager();

})(window);