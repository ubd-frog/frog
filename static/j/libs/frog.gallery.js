

Frog.Gallery = new Class({
    Implements: [Events, Options],
    options: {},
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
        var uploaderElement = $('upload');

        // -- Members
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
        this.requestData = {};
        this.spinner = new Spinner(undefined, {message: "fetching images..."});

        // -- Events
        window.addEvent('scroll', this._scroll.bind(this));
        window.addEvent('resize', this.resize.bind(this));
        window.addEventListener('hashchange', this.historyEvent.bind(this), false)
        this.container.addEvent('click:relay(a.frog-tag)', function(e, el) {
            self.filter(el.dataset.frog_tag_id);
        });
        this.container.addEvent('click:relay(a.frog-image-link)', this.viewImages.bind(this));
        this.container.addEventListener('dragenter', function() {
            uploaderElement.show();
            self._uploaderList();
            self.uploaderList.show();
        }, false);

        // -- Instance objects
        this.controls = new Frog.Gallery.Controls(this.toolsElement, this.id);
        this.controls.addEvent('remove', this.removeItems.bind(this))
        this._uploader();
        this.viewer = new Frog.Viewer();
        
        var builderData;
        if (location.hash !== "") {
            data = JSON.parse(location.hash.split('#')[1]);
            builderData = data.filters;
        }
        this.builder = new Frog.QueryBuilder({
            data: builderData,
            onChange: function(data) {
                self.setFilters(data)
            }
        });
        $(this.builder).inject(this.container, 'before')
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
        // var data = {
        //     filters: [
        //         [val]
        //     ]
        // };
        // location.hash = JSON.stringify(data);
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

        this.requestData.models = 'image';
        
        var self = this;
        new Request.JSON({
            url: '/frog/gallery/1/filter',
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
                        var t = new Frog.Thumbnail(self.objects.length - 1, o.width, o.height, {
                            title: o.title,
                            artist: o.author.first + ' ' + o.author.last,
                            tags: o.tags,
                            image: o.thumbnail,
                            imageID: o.id,
                            guid: o.guid
                        });
                        self.thumbnails.push(t);
                        t.setSize(self.tileSize);
                        self.container.grab($(t));
                    });
                    self._getScreen();
                }
                self.isRequesting = false;
                self.spinner.hide();
            }
        }).GET(this.requestData);
    },
    resize: function() {
        this.tileSize = (window.getWidth() - 2) / this.tilesPerRow;
        this.thumbnails.each(function(t) {
            t.setSize(this.tileSize);
        }, this)
    },
    historyEvent: function(e) {
        var key = (typeOf(e) === 'string') ? e : e.newURL;
        var data = JSON.parse(unescape(key.split('#')[1]));
        data.filters = JSON.stringify(data.filters);
        if (typeof data.viewer === 'undefined') {
            this.viewer.hide();
        }
        if (data.filters !== this.requestData.filters || !this.requestData.filters) {
            this.request(data)
        }
    },
    removeItems: function(ids) {
        var guids = [];
        var r = confirm('Are you sure you wish to remove (' + ids.length + ') items from the gallery?');
        if (r) {
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
                        }, this)
                    }
                }.bind(this)
            }).DELETE({guids: guids.join(',')});
        }
    },
    viewImages: function(e, el) {
        e.stop();
        var selection = $$('.thumbnail.selected');
        var id = el.parentNode.parentNode.dataset.frog_tn_id;
        var objects = [];
        if (selection.length) {
            this.thumbnails[id].setSelected(true);
            objects.push(this.objects[id]);
            selection.each(function(item) {
                var idx = item.dataset.frog_tn_id;
                objects.push(this.objects[idx]);
            }, this);
            objects = objects.unique();
            this.viewer.setImages(objects);
        }
        else {
            var objects = Array.clone(this.objects);
            this.viewer.setImages(objects, id);
        }
        
        this.viewer.fitToWindow();
        this.viewer.show();
    },
    _uploader: function() {
        var self = this;
        if (typeOf(this.uploader) === 'null') {
            var uploader = new plupload.Uploader({
                runtimes: 'html5',
                browse_button: 'frogBrowseButton',
                drop_element: 'upload',
                container: 'upload',
                max_file_size: '100mb',
                url: '/frog/',
                headers: {"X-CSRFToken": Cookie.read('csrftoken')},
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
                var uploaderElement = $('upload');
                if (!uploaderElement.isVisible()) {
                    uploaderElement.show();
                    self._uploaderList();
                    self.uploaderList.show();
                }
                var ul = $('upload_list');
                files.each(function(f) {
                    self.uploaderList.store.add({
                        id: f.id,
                        file: f.name,
                        size: f.size,
                        percent: 0
                    });
                })
            });

            uploader.bind('UploadProgress', function(up, file) {
                self.uploaderList.store.getById(file.id).set('percent', file.percent);
            });

            uploader.bind('UploadComplete', function(up, files) {
                $('upload').hide();
                self.uploaderList.store.removeAll();
                self.uploaderList.hide();
                self.request();
            });

            this.uploader = uploader;
        }

        return this.uploader;
    },
    _uploaderList: function() {
        var self = this;
        if (this.uploaderList) {
            return this.uploaderList;
        }
        Ext.require(['*']);
        var store = Ext.create('Ext.data.ArrayStore', {
            fields: [
                {name: 'id'},
                {name: 'file'},
                {name: 'size', type: 'int'},
                {name: 'percent', type: 'int'}
            ]
        });
        var grid = DEBUG = Ext.create('Ext.grid.Panel', {
            store: store,
            columns: [
                {
                    text     : 'File',
                    flex     : 6,
                    sortable : false,
                    dataIndex: 'file'
                },
                {
                    text     : 'Size',
                    flex     : 1,
                    sortable : false,
                    dataIndex: 'size'
                },
                {
                    text     : '%',
                    flex     : 1,
                    sortable : false,
                    dataIndex: 'percent'
                }
            ],
            height: 350,
            width: '100%',
            title: 'Files to Upload',
            renderTo: 'upload_files',
            viewConfig: {
                stripeRows: true
            }
        });

        var uploadButton = Ext.create('Ext.Button', {
            text: 'Upload Files',
            renderTo: 'upload_files',
            scale: 'large',
            handler: function() {
                self.uploader.start();
            }
        });
        var uploadButton = Ext.create('Ext.Button', {
            text: 'Cancel',
            renderTo: 'upload_files',
            scale: 'large',
            handler: function() {
                $('upload').hide();
                self.uploaderList.store.removeAll();
                self.uploaderList.hide();
            }
        });

        this.uploaderList = grid;
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
});


Frog.Gallery.Controls = new Class({
    Implements: Events,
    initialize: function(el, id) {
        var self = this;
        this.id = id;
        Ext.require(['*']);
        this.toolbar = Ext.create('Ext.toolbar.Toolbar');
        this.toolbar.render(el);
        this.bUpload = this.toolbar.add({
            id: 'frogBrowseButton',
            text: 'Upload',
            icon: '/static/i/add.png'
        });
        this.bEditTags = this.toolbar.add({
            text: 'Edit Tags',
            icon: '/static/i/tag_orange.png',
            handler: function() {
                var guids = [];
                $$('.selected').each(function(item) {
                    guids.push(item.dataset.frog_guid);
                });
                var win = Ext.create('widget.window', {
                    title: 'Edit Tags',
                    closable: true,
                    resizable: false,
                    modal: true,
                    width: 600,
                    height: 450,
                    layout: 'border',
                    bodyStyle: 'padding: 5px;',
                    items: [{
                        loader: {
                            url: '/frog/tag/manage?guids=' + guids.join(','),
                            contentType: 'html',
                            loadMask: true,
                            autoLoad: true,
                            scripts: true,
                            cache: false
                        }
                    }],
                    buttons: [{
                        text: 'Save',
                        handler: function() {
                            var add = [], rem = [];
                            $$('#frog_add li').each(function(item) {
                                var id = item.dataset.frog_tag_id;
                                add.push(id);
                            });
                            $$('#frog_rem li').each(function(item) {
                                var id = item.dataset.frog_tag_id;
                                rem.push(id);
                            });
                            
                            new Request.JSON({
                                url: '/frog/tag/manage',
                                headers: {"X-CSRFToken": Cookie.read('csrftoken')}
                            }).POST({
                                add: add.join(','),
                                rem: rem.join(','),
                                guids: guids.join(',')
                            });
                            win.close();
                        }
                    },{
                        text: 'Cancel',
                        handler: function() {
                            win.close();
                        }
                    }]
                });
                win.show();
            }
        });
        this.mRemove = Ext.create('Ext.menu.Item', {
            text: 'Remove Selected',
            icon: '/static/i/cross.png',
            handler: function() {
                var ids = [];
                $$('.selected').each(function(item) {
                    ids.push(item.dataset.frog_tn_id.toInt());
                });
                self.fireEvent('onRemove', [ids])
            }
        });
        // this.mCopy = Ext.create('Ext.menu.Item', {
        //     text: 'Copy to gallery'
        // });
        this.mDownload = Ext.create('Ext.menu.Item', {
            text: 'Download Sources',
            icon: '/static/i/compress.png',
            handler: function() {
                var selected = $$('.thumbnail.selected');
                guids = [];
                selected.each(function(item) {
                    guids.push(item.dataset.frog_guid);
                });
                location.href = '/frog/download?guids=' + guids.join(',');
            }
        });
        // this.mSwitchArtist = Ext.create('Ext.menu.Item', {
        //     text: 'Switch Artist'
        // });
        
        var m = Ext.create('Ext.menu.Menu', {
            items: [this.mRemove, this.mDownload]
        });
        
        this.toolbar.add({
            text: 'Manage',
            icon: '/static/i/photos.png',
            menu: m
        });

        this.bRSS = this.toolbar.add({
            icon: '/static/i/feed.png',
            handler: function() {
                var win = Ext.create('widget.window', {
                    closable: true,
                    closeAction: 'hide',
                    resizable: false,
                    modal: true,
                    width: 300,
                    height: 150,
                    layou1t: 'border',
                    bodyStyle: 'padding: 5px;'
                });
                win.show();
                var fp = Ext.create('Ext.FormPanel', {
                    title: 'RSS Feeds',
                    defaultType: 'radio',
                    items: [{
                        boxLabel: 'Daily',
                        name: 'rss_int',
                        inputValue: 'daily'
                    }, {
                        checked: true,
                        boxLabel: 'Weekly',
                        name: 'rss_int',
                        inputValue: 'weekly'
                    }],
                    buttons: [{
                        text: 'Save',
                        handler: function() {
                            var r = fp.getForm().getValues(true).split('=')[1];
                            location.href = 'feed://' + location.host + '/frog/rss/' + self.id + '/' + r;
                            win.close();
                        }
                    },{
                        text: 'Cancel',
                        handler: function() {
                            win.close();
                        }
                    }]
                });
                win.add(fp)
            }
        });
        // this.bHelp = this.toolbar.add({
        //     icon: '/static/i/help.png',
        // });
        // this.bPreferences = this.toolbar.add({
        //     icon: '/static/i/cog.png',
        // });
    }
})