/*
Copyright (c) 2012 Brett Dixon

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
Software, and to permit persons to whom the Software is furnished to do so, 
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/


Frog.Gallery = new Class({
    Implements: [Events, Options],
    options: {
        private: false,
        upload: true,
        altclick: false
    },
    initialize: function(el, id, options) {
        var self = this;
        this.setOptions(options);
        this.id = id;

        // -- Elements
        this.el = (typeof el === 'undefined' || typeOf(el) === 'null') ? $(document.body) : $(el);
        this.container = new Element('div', {
            id: 'gallery'
        }).inject(this.el);
        this.toolsElement = new Element('div', {id: 'frog_tools'}).inject(this.container, 'before');

        // -- Members
        this.tilesPerRow = Frog.Prefs.tileCount;
        this.tileSize = Math.floor((window.getWidth() - 2) / this.tilesPerRow);
        this.objects = [];
        this.thumbnails = [];
        this.y = 0;
        this.timer = this._scrollTimer.periodical(30, this);
        this.dirty = true;
        this.requestValue = {};
        this.isRequesting = false;
        this.requestData = {};
        this.spinner = new Spinner(undefined, {message: "fetching images...", fxOptions: {duration: 0}});

        // -- Events
        window.addEvent('scroll', this._scroll.bind(this));
        window.addEvent('resize', this.resize.bind(this));
        window.addEventListener('hashchange', this.historyEvent.bind(this), false)
        this.container.addEvent('click:relay(a.frog-tag)', function(e, el) {
            self.filter(el.dataset.frog_tag_id);
        });
        this.container.addEvent('click:relay(a.frog-image-link)', this.viewImages.bind(this));
        Frog.Comments.addEvent('post', function(id) {
            var commentEl = $(self.thumbnails[id]).getElements('.frog-comment-bubble')[0];
            var count = commentEl.get('text').toInt();
            commentEl.set('text', count + 1);
        })

        // -- Instance objects
        Frog.UI.addEvent('remove', this.removeItems.bind(this));
        Frog.UI.addEvent('change', function() {
            self.tilesPerRow = Frog.Prefs.tileCount;
            self.tileSize = Math.floor((window.getWidth() - 2) / self.tilesPerRow);
            self.request();
        });
        if (options.private) {
            Frog.UI.addPrivateMenu();
        }
        if (this.options.upload) {
            Frog.UI.enableUploads();
        }

        Frog.UI.setId(this.id);
        Frog.UI.render(this.toolsElement);

        if (this.options.upload) {
            var uploaderElement = $('upload');
            this.uploader = new Frog.Uploader(this.id);
            this.uploader.addEvent('complete', function() {
                this.request();
            }.bind(this));
        }

        
        this.viewer = new Frog.Viewer();
        this.viewer.addEvent('show', function() {
            window.scrollTo(0,0);
            self.container.setStyle('height', 0);
            self.selector.deactivate();
        }.bind(this));
        this.viewer.addEvent('hide', function() {
            self.container.setStyle('height', 'auto')
            window.scrollTo(0,this.y);
            self.selector.activate();
        }.bind(this));
        this.keyboard = new Keyboard({
            active: true,
            events: {
                'ctrl+a': function(e) { e.stop(); $$('.thumbnail').addClass('selected'); },
                'ctrl+d': function(e) { e.stop(); $$('.thumbnail').removeClass('selected'); }
            }
        });

        this.selector = new Selection(this.container, {
            selector: '.thumbnail',
            ignore: ['a', 'span']
        });
        
        var builderData;
        if (location.hash !== "") {
            data = JSON.parse(location.hash.split('#')[1]);
            builderData = data.filters;
        }
        var bucketHeight = 50;
        this.builder = new Frog.QueryBuilder({
            data: builderData,
            onChange: function(data) {
                self.setFilters(data)
            },
            onAdd: function() {
                var pad = self.container.getStyle('padding-top').toInt();
                self.container.setStyle('padding-top', pad + bucketHeight);
            },
            onRemove: function() {
                var pad = self.container.getStyle('padding-top').toInt();
                var height = Math.max(bucketHeight, pad - bucketHeight)
                self.container.setStyle('padding-top', height);
            }
        });
        $(this.builder).inject(this.container, 'before');
        //this.builder.sortables.addLists($$('.frog-bucket'));
    },
    clear: function() {
        this.objects = [];
        this.thumbnails = [];
        this.container.empty();
    },
    filter: function(id) {
        var val = id.toInt();
        if (typeOf(val) === "null") {
            val = id;
        }
        this.builder.addTag(0, val);
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
        this.requestData = data || this.requestData;
        if (append) {
            this.requestData.more = true;
        }
        this.requestData.models = [];
        if (Frog.Prefs.include_image) {
            this.requestData.models.push('image');
        }
        if (Frog.Prefs.include_video) {
            this.requestData.models.push('video');
        }
        this.requestData.models = this.requestData.models.unique().join(',');
        
        var self = this;
        new Request.JSON({
            url: '/frog/gallery/' + this.id + '/filter',
            noCache: true,
            onRequest: function() {
                self.isRequesting = true;
                self.spinner.show();
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
                        var t = new Frog.Thumbnail(self.objects.length - 1, o, {
                            artist: o.author.first + ' ' + o.author.last,
                            imageID: o.id
                        });
                        self.thumbnails.push(t);
                        t.setSize(self.tileSize);
                        self.container.grab($(t));
                    });
                    window.scrollTo(0,0);
                    self._getScreen();
                }
                self.isRequesting = false;
                self.spinner.hide();
            }
        }).GET(this.requestData);
    },
    resize: function() {
        this.tileSize = Math.floor((window.getWidth() - 2) / this.tilesPerRow);
        this.thumbnails.each(function(t) {
            t.setSize(this.tileSize);
        }, this);
        this._getScreen();
    },
    historyEvent: function(e) {
        var key = (typeOf(e) === 'string') ? e : e.newURL;
        var data = JSON.parse(unescape(key.split('#')[1]));
        data.filters = JSON.stringify(data.filters);
        if (typeof data.viewer === 'undefined' && this.viewer.isOpen) {
            this.viewer.hide();
        }
        if (data.filters !== this.requestData.filters || !this.requestData.filters) {
            this.request(data)
        }
        if (this.builder) {
            this.builder.clean();
        }
    },
    removeItems: function(data) {
        var ids = data.ids;
        var silent = data.silent;

        if (ids.length === 0) {
            Ext.MessageBox.alert('Selection', 'Please select items first!');

            return false;
        }
        var guids = [];
        if (silent) {
            this._removeItems(ids);
        }
        else {
            var r = Ext.MessageBox.confirm(
                'Remove Items',
                'Are you sure you wish to remove (' + ids.length + ') items from the gallery?',
                function(r) {
                    if (r === 'yes') {
                        this._removeItems(ids);
                    }
                }.bind(this)
            );
        }
    },
    viewImages: function(e, el) {
        e.stop();
        if (this.options.altclick && e.control) {
            var id = el.parentNode.parentNode.dataset['frog_tn_id'].toInt();
            this.options.altclick(this.objects[id]);

            return true;
        }
        
        this.y = window.getScroll().y;
        var selection = $$('.thumbnail.selected');
        var id = (Browser.ie) ? el.parentNode.parentNode.getProperty('dataset-frog_tn_id') : el.parentNode.parentNode.dataset.frog_tn_id;
        var objects = [];
        if (selection.length) {
            this.thumbnails[id].setSelected(true);
            selection = $$('.thumbnail.selected');
            selection.each(function(item, selID) {
                var idx = (Browser.ie) ? item.getProperty('dataset-frog_tn_id') : item.dataset.frog_tn_id;
                if (idx === id) {
                    id = selID;
                }
                objects.push(this.objects[idx]);
            }, this);
            objects = objects.unique();
            this.viewer.show();
            this.viewer.setImages(objects, id);
        }
        else {
            var objects = Array.clone(this.objects);
            this.viewer.show();
            this.viewer.setImages(objects, id);

        }
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
        
        if (heightDelta < window.getHeight() + buffer && this.requestValue.count > 0 && !this.viewer.isOpen) {
            this.request(undefined, true)
        }
    },
    _scrollTimer: function() {
        if (this.dirty) {
            this._getScreen();
        }
    },
    _removeItems: function(ids) {
        var guids = [];
        ids.each(function(id) {
            guids.push(this.objects[id].guid);
        }, this);

        new Request.JSON({
            url: location.href,
            emulation: false,
            headers: {"X-CSRFToken": Cookie.read('csrftoken')},
            onSuccess: function(res) {
                if (res.isSuccess) {
                    ids.each(function(id) {
                        $(this.thumbnails[id]).destroy();
                        this.thumbnails.erase(id);
                    }, this);
                }
            }.bind(this)
        }).DELETE({guids: guids.join(',')});

        this.dirty = true;
    }
});
