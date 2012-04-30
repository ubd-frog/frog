

Frog.Gallery = new Class({
    Implements: [Events, Options],
    options: {},
    initialize: function(el, id, options) {
        var self = this;
        this.setOptions(options);
        this.el = (typeof el === 'undefined' || typeOf(el) === 'null') ? $(document.body) : $(el);
        this.id = id;
        this.container = new Element('div', {
            id: 'gallery'
        }).inject(this.el);
        // this.searchEl = new Element('div', {id: 'search_el'}).inject(this.container, 'before');
        // var search = new Element('input', {
        //     type: 'search',
        //     events: {
        //         keydown: function(e) {
        //             if (e.code === 13) {
        //                 self.filter(this.value)
        //             }
        //         }
        //     }
        // }).inject(this.searchEl);

        this.tilesPerRow = 6;
        this.tileSize = (window.getWidth() - 2) / this.tilesPerRow;

        this.objects = [];
        this.thumbnails = [];
        this.y = 0;
        this.timer = this._scrollTimer.periodical(300, this);
        this.dirty = true;
        this.requestValue = {};
        this.isRequesting = false;
        this.uploader = null;

        window.addEvent('scroll', this._scroll.bind(this));
        window.addEvent('resize', this.resize.bind(this));
        window.addEventListener('hashchange', this.historyEvent.bind(this), false)
        this.container.addEvent('click:relay(a)', function(e, el) {
            self.filter(el.dataset.frog_tag_id);
        });
        this._uploader();

        var up = $('upload');
        up.hide();
        this.container.addEventListener('dragenter', function() {
            console.log('enter');
            up.show();
        }, false);

        
        var builderData;
        if (location.hash !== "") {
            data = JSON.parse(location.hash.split('#')[1]);
            builderData = data.filters;
        }

        this.builder = new Frog.QueryBuilder({
            data: builderData,
            onChange: function(data) {
                //console.log(JSON.stringify(data));
                self.setFilters(data)
            }
        });
        $(this.builder).inject(this.container, 'before')
        //this.builder.addBucket();
    },
    clear: function() {
        this.objects = [];
        this.container.empty();
    },
    filter: function(id) {
        var val = id.toInt();
        if (typeOf(val) === "null") {
            val = id;
        }
        var data = {
            tags: [
                [val]
            ]
        };
        location.hash = JSON.stringify(data);
    },
    setFilters: function(obj) {
        var data = {};
        data.filters = (obj) ? obj : [];
        var oldHash = location.hash;
        location.hash = JSON.stringify(data);
        if (oldHash === location.hash) {
            this.historyEvent(location.hash)
        }
    },
    request: function(data, append) {
        if (this.isRequesting) {
            return;
        }
        append = (typeof(append) === 'undefined') ? false : append;
        data = data || {};
        if (append) {
            data.more = true;
        }
        
        var self = this;
        new Request.JSON({
            url: '/frog/gallery/1/filter',
            onRequest: function() {
                self.isRequesting = true;
            },
            onSuccess: function(res) {
                self.requestValue = res.value;
                if (res.isSuccess) {
                    if (!append) {
                        self.clear();
                        if (res.values.length === 0) {
                            self.container.set('text', 'Nothing Found')
                        }
                    }
                    res.values.each(function(o) {
                        self.objects.push(o);
                        var t = new Frog.Thumbnail(self.objects.length - 1, o.width, o.height, {
                            title: o.title,
                            artist: o.author.first + ' ' + o.author.last,
                            tags: o.tags,
                            image: o.thumbnail,
                            imageID: o.id,
                            onSelect: function() {
                                this.element.addClass('selected')
                            }
                        });
                        self.thumbnails.push(t);
                        t.setSize(self.tileSize);
                        self.container.grab($(t));
                    });
                    self._getScreen();
                }
                self.isRequesting = false;
            }
        }).GET(data);
    },
    resize: function() {
        this.tileSize = (window.getWidth() - 2) / this.tilesPerRow;
        this.thumbnails.each(function(t) {
            t.setSize(this.tileSize);
        }, this)
    },
    historyEvent: function(e) {
        var key = (typeOf(e) === 'string') ? e : e.newURL;
        var data = JSON.parse(key.split('#')[1]);
        data.filters = JSON.stringify(data.filters);
        this.request(data)
    },
    _uploader: function() {
        if (typeOf(this.uploader) === 'null') {
            var uploader = new plupload.Uploader({
                runtimes: 'html5',
                browse_button: 'upload_browse',
                drop_element: 'upload_drop',
                container: 'upload',
                max_file_size: '100mb',
                url: '/frog/',
                multipart_params: {
                    'galleries': this.id.toString()
                },
                filters: [
                    {title: "Image files", extensions: "jpg,png"},
                    {title: "Video files", extensions: "mp4,avi,mov"}
                ]
            });

            uploader.bind('Init', function(up, files) {

            });

            uploader.init();

            uploader.bind('FilesAdded', function(up, files) {
                var ul = $('upload_list');
                files.each(function(f) {
                    new Element('li', {id: f.id, text: f.name}).inject(ul);
                })
            });

            uploader.bind('UploadProgress', function(up, file) {
                var el = $(file.id);
                el.set('text', file.name + ' ' + file.percent)
            });

            $('upload_start').addEvent('click', function(e) {
                e.stop();
                uploader.start();
            })

            this.uploader = uploader;
        }

        return this.uploader;
    },
    _getScreen: function() {
        var s, e, t, row, endRow;

        row = Math.floor(window.getScroll().y / (this.tileSize + 30));
        s = row * this.tilesPerRow;
        endRow = row + Math.floor(window.getHeight() / (this.tileSize + 30));
        e = endRow * this.tilesPerRow + this.tilesPerRow;

        for (var i=s;i<e;i++) {
            t = this.thumbnails[i]
            if (t) {
                t.load();
                $(t).addClass('loaded');
            }
        }

        this.dirty = false;
    },
    _scroll: function () {
        clearTimeout(this.timer);
        this.timer = this._scrollTimer.periodical(300, this);
        this.dirty = true;
        var heightDelta = this.container.getHeight() - window.getScroll().y;
        var buffer = 300;
        
        if (heightDelta < window.getHeight() + buffer && this.requestValue.count > 0) {
            this.request(undefined, true)
        }
    },
    _scrollTimer: function() {
        if (this.dirty) {
            this._getScreen();
        }
    }
})