

Frog.Gallery = new Class({
    Implements: [Events, Options],
    options: {private: false},
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
        this.tilesPerRow = Frog.Prefs.tileCount;
        this.tileSize = Math.floor((window.getWidth() - 2) / this.tilesPerRow);
        this.objects = [];
        this.thumbnails = [];
        this.y = 0;
        this.timer = this._scrollTimer.periodical(30, this);
        this.dirty = true;
        this.requestValue = {};
        this.isRequesting = false;
        this.uploader = null;
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
        this.controls = new Frog.Gallery.Controls(this.toolsElement, this.id);
        this.controls.addEvent('remove', this.removeItems.bind(this));
        this.controls.addEvent('change', function() {
            self.tilesPerRow = Frog.Prefs.tileCount;
            self.tileSize = Math.floor((window.getWidth() - 2) / self.tilesPerRow);
            self.request();
        });
        if (options.private) {
            this.controls.addPrivateMenu();
        }

        this.uploader = new Frog.Uploader(this.id);
        this.uploader.addEvent('complete', function() {
            this.request();
        }.bind(this));
        this.viewer = new Frog.Viewer();
        this.viewer.addEvent('show', function() {
            window.scrollTo(0,0);
            self.container.setStyle('height', 0)
        }.bind(this));
        this.viewer.addEvent('hide', function() {
            self.container.setStyle('height', 'auto')
            this.resize();
            window.scrollTo(0,this.y);
        }.bind(this));
        this.keyboard = new Keyboard({
            active: true,
            events: {
                'ctrl+a': function(e) { e.stop(); $$('.thumbnail').addClass('selected'); },
                'ctrl+d': function(e) { e.stop(); $$('.thumbnail').removeClass('selected'); }
            }
        })
        
        var builderData;
        if (location.hash !== "") {
            data = JSON.parse(location.hash.split('#')[1]);
            builderData = data.filters;
        }
        var bucketHeight = 30;
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
                self.container.setStyle('padding-top', pad - bucketHeight);
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

        // -- Models
        Ext.define('Gallery', {
            extend: 'Ext.data.Model',
            fields: [
                {name: 'id'},
                {name: 'title'},
                {name: 'image_count', type: 'int'},
                {name: 'video_count', type: 'int'},
                {name: 'owner'},
                {name: 'description'},
                {name: 'private'}
            ]
        });

        this.galleryStore = Ext.create('Ext.data.Store', {
            autoLoad: true,
            autoSync: true,
            model: 'Gallery',
            proxy: {
                type: 'ajax',
                url: '/frog/gallery',
                reader: {
                    type: 'json',
                    root: 'values'
                }
            }
        });

        this.toolbar = Ext.create('Ext.toolbar.Toolbar');
        this.toolbar.render(el);
        var navMenu = Ext.create('Ext.menu.Menu');
        this.bNav = this.toolbar.add({
            text: 'Navigation',
            icon: FrogStaticRoot + '/frog/i/compass.png',
            menu: navMenu
        });
        navMenu.add(this.getNavMenu());
        this.bUpload = this.toolbar.add({
            id: 'frogBrowseButton',
            text: 'Upload',
            icon: FrogStaticRoot + '/frog/i/add.png'
        });
        this.bEditTags = this.toolbar.add({
            text: 'Edit Tags',
            icon: FrogStaticRoot + '/frog/i/tag_orange.png',
            handler: function() {
                var guids = [];
                $$('.selected').each(function(item) {
                    guids.push(item.dataset.frog_guid);
                });
                var win = Ext.create('widget.window', {
                    title: 'Edit Tags',
                    icon: FrogStaticRoot + '/frog/i/tag_orange.png',
                    closable: true,
                    resizable: false,
                    modal: true,
                    width: 800,
                    height: 600,
                    layout: 'fit',
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
                                headers: {"X-CSRFToken": Cookie.read('csrftoken')},
                                onSuccess: function() {
                                    add.each(function(tag) {
                                        Frog.Tags.get(tag);
                                    });
                                }
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
            icon: FrogStaticRoot + '/frog/i/cross.png',
            handler: function() {
                var ids = [];
                $$('.selected').each(function(item) {
                    ids.push(item.dataset.frog_tn_id.toInt());
                });
                self.fireEvent('onRemove', [ids])
            }
        });
        this.mCopy = Ext.create('Ext.menu.Item', {
            text: 'Copy to Gallery',
            icon: FrogStaticRoot + '/frog/i/page_white_copy.png',
            handler: function() {
                var win = Ext.create('widget.window', {
                    title: 'Copy to Gallery',
                    icon: FrogStaticRoot + '/frog/i/page_white_copy.png',
                    closable: true,
                    //closeAction: 'hide',
                    resizable: false,
                    modal: true,
                    width: 600,
                    height: 300,
                    bodyStyle: 'padding: 5px;'
                });
                win.show();

                var fp = Ext.create('Ext.FormPanel', {
                    items: [{
                        xtype: 'label',
                        text: "Copy images to a new Gallery:"
                    }, {
                        xtype:'fieldset',
                        title: 'New Gallery',
                        items: [
                            {
                                fieldLabel: 'Title',
                                xtype: 'textfield',
                                name: 'title'

                            }, {
                                fieldLabel: 'Description',
                                xtype: 'textfield',
                                name: 'description'
                            }, {
                                fieldLabel: 'Private?',
                                xtype: 'checkbox',
                                name: 'private'
                            }
                        ]
                    }, {
                        xtype: 'label',
                        text: 'Or choose an existing one:'
                    }, {
                        xtype:'fieldset',
                        title: 'Existing Gallery',
                        items: [
                            {
                                xtype: 'combobox',
                                editable: false,
                                store: self.galleryStore,
                                displayField: 'title',
                                valueField: 'id',
                                id: 'frog_gallery_id'
                            }
                        ]
                    }],
                    buttons: [{
                        text: 'Send',
                        handler: function() {
                            var data = fp.getForm().getValues();
                            data.id = data['frog_gallery_id-inputEl'];
                            if (data.title !== "") {
                                var private = (data.private === 'on') ? true : false;
                                new Request.JSON({
                                    url: '/frog/gallery',
                                    async: false,
                                    onSuccess: function(res) {
                                        data.id = res.value.id;
                                    }
                                }).POST({title: data.title, description: data.description, private: private});
                            }
                            var selected = $$('.thumbnail.selected');
                            guids = [];
                            selected.each(function(item) {
                                guids.push(item.dataset.frog_guid);
                            });
                            new Request.JSON({
                                url: '/frog/gallery/' + data.id,
                                emulation: false,
                                async: false,
                                onSuccess: function(res) {
                                    self.galleryStore.sync();
                                    Ext.MessageBox.confirm('Confirm', 'Would you like to visit this gallery now?', function(res) {
                                        if (res === 'yes') {
                                            window.location = '/frog/gallery/' + data.id;
                                        }
                                    });
                                }
                            }).PUT({guids: guids.join(',')});
                            win.close();
                        }
                    },{
                        text: 'Cancel',
                        handler: function() {
                            win.close();
                        }
                    }]
                });
                win.add(fp);
            }
        });
        this.mDownload = Ext.create('Ext.menu.Item', {
            text: 'Download Sources',
            icon: FrogStaticRoot + '/frog/i/compress.png',
            handler: function() {
                var selected = $$('.thumbnail.selected');
                guids = [];
                selected.each(function(item) {
                    guids.push(item.dataset.frog_guid);
                });
                location.href = '/frog/download?guids=' + guids.join(',');
            }
        });
        this.mSwitchArtist = Ext.create('Ext.menu.Item', {
            text: 'Switch Artist',
            icon: FrogStaticRoot + '/frog/i/user_edit.png',
            handler: function() {
                var win = Ext.create('widget.window', {
                    title: 'Switch Artist',
                    closable: true,
                    closeAction: 'hide',
                    resizable: false,
                    modal: true,
                    width: 400,
                    height: 200,
                    bodyStyle: 'padding: 5px;'
                });
                win.show();
                var input = new Element('input', {placeholder: "Search"});

                var fp = Ext.create('Ext.FormPanel', {
                    items: [{
                        xtype: 'label',
                        text: "Start typing the name of an artist or if this is a new artist, type in the first and last name and click Send"
                    }, {
                        xtype: 'textfield',
                        fieldLabel: 'Artist Name',
                        id: 'frog_switch_artist'
                    }],
                    buttons: [{
                        text: 'Send',
                        handler: function() {
                            self.switchArtistCallback(input.value);
                            win.close();
                        }
                    },{
                        text: 'Cancel',
                        handler: function() {
                            win.close();
                        }
                    }]
                });
                win.add(fp);
                var input = $('frog_switch_artist-inputEl');
                new Meio.Autocomplete(input, '/frog/artistlookup', {
                    requestOptions: {
                        headers: {"X-CSRFToken": Cookie.read('csrftoken')},
                    },
                    filter: {
                        path: 'name',
                        formatItem: function(text, data) {
                            if (data.id === 0) {
                                return '<span class="search"></span>' + data.name
                            }
                            else {
                                return '<span></span>' + data.name
                            }
                        }
                    }
                });
                input.focus();
            }
        });
        
        this.menu = Ext.create('Ext.menu.Menu', {
            items: [this.mRemove, this.mCopy, this.mDownload, '-', this.mSwitchArtist]
        });
        
        this.toolbar.add({
            text: 'Manage',
            icon: FrogStaticRoot + '/frog/i/photos.png',
            menu: this.menu
        });
        this.toolbar.add('-')
        this.bRSS = this.toolbar.add({
            icon: FrogStaticRoot + '/frog/i/feed.png',
            handler: function() {
                var win = Ext.create('widget.window', {
                    title: 'RSS Feeds',
                    icon: FrogStaticRoot + '/frog/i/feed.png',
                    closable: true,
                    closeAction: 'hide',
                    resizable: false,
                    modal: true,
                    width: 400,
                    height: 200,
                    bodyStyle: 'padding: 5px;'
                });
                win.show();
                var fp = Ext.create('Ext.FormPanel', {
                    defaultType: 'radio',
                    items: [{
                        xtype: 'label',
                        text: "Select a feed frequency you'd like to subscribe to and the images will be available through Outlook"
                    },
                    {
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
        this.bHelp = this.toolbar.add({
            icon: FrogStaticRoot + '/frog/i/help.png',
            handler: function() {
                var win = Ext.create('widget.window', {
                    title: 'Ask for Help',
                    icon: FrogStaticRoot + '/frog/i/help.png',
                    closable: true,
                    closeAction: 'hide',
                    resizable: false,
                    modal: true,
                    width: 400,
                    bodyPadding: 10,
                    bodyStyle: 'padding: 5px; background: transparent;'
                });
                win.show();
                var fp = Ext.create('Ext.FormPanel', {
                    items: [{
                        xtype: 'label',
                        text: "Have a question, problem or suggestion?"
                    },
                    {
                        xtype     : 'textareafield',
                        grow      : true,
                        name      : 'message',
                        anchor    : '100%'
                    }],
                    buttons: [{
                        text: 'Send',
                        handler: function() {
                            var data = fp.getForm().getValues();
                            new Request({
                                url: '/frog/help/',
                                headers: {"X-CSRFToken": Cookie.read('csrftoken')}
                            }).POST(data);
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
        var prefMenu = this.getPrefMenu();
        this.bPreferences = this.toolbar.add({
            icon: FrogStaticRoot + '/frog/i/cog.png',
            menu: prefMenu
        });
    },
    addPrivateMenu: function() {
        var id = this.id;
        this.menu.add({
            text: 'Make public',
            icon: FrogStaticRoot + '/frog/i/page_white_copy.png',
            handler: function() {
                Ext.MessageBox.confirm('Confirm', 'Are you sure you want to make this public?', function(res) {
                    if (res === 'yes') {
                        new Request.JSON({
                            url: '/frog/gallery/' + id,
                            emulation: false,
                            headers: {"X-CSRFToken": Cookie.read('csrftoken')}
                        }).PUT({private: false})
                    }
                });
            }
        });
    },
    getPrefMenu: function() {
        var self = this;
        var colorMenu = Ext.create('Ext.menu.ColorPicker', {
            height: 24,
            handler: function(cm, color){
                Frog.Prefs.set('backgroundColor', JSON.stringify('#' + color));
            }
        });
        colorMenu.picker.colors = ['000000', '424242', '999999', 'FFFFFF'];
        var tileSizeHandler = function(item, checked) {
            var size = item.value;
            Frog.Prefs.set('tileCount', size);
            item.parentMenu.hide();
            self.fireEvent('onChange', [Frog.Prefs]);
        }
        var batchSize = Ext.create('Ext.form.field.Number', {
            value: Frog.Prefs.batchSize,
            minValue: 0,
            maxValue: 500
        });
        batchSize.on('change', function(field, val) { 
            Frog.Prefs.set('batchSize', val);
        });

        var menu = Ext.create('Ext.menu.Menu', {
            items: [
                {
                    text: 'Viewer Background',
                    menu: colorMenu
                },
                {
                    text: 'Thumbnail Size',
                    menu: [
                        {
                            text: 'Large (6)',
                            value: 6,
                            checked: Frog.Prefs.tileCount === 6,
                            group: 'theme',
                            checkHandler: tileSizeHandler
                        }, {
                            text: 'Medium (9)',
                            value: 9,
                            checked: Frog.Prefs.tileCount === 9,
                            group: 'theme',
                            checkHandler: tileSizeHandler
                        }, {
                            text: 'Small (12)',
                            value: 12,
                            checked: Frog.Prefs.tileCount === 12,
                            group: 'theme',
                            checkHandler: tileSizeHandler
                        }
                    ]
                },
                {
                    text: 'Item Request Size',
                    menu: [
                        batchSize
                    ]
                }, {
                    xtype: 'menucheckitem',
                    text: 'Include Images',
                    checked: Frog.Prefs.include_image,
                    checkHandler: function(item, checked) {
                        Frog.Prefs.set('include_image', checked);
                        item.parentMenu.hide();
                        self.fireEvent('onChange', [Frog.Prefs]);
                    }
                }, {
                    xtype: 'menucheckitem',
                    text: 'Incude Video',
                    checked: Frog.Prefs.include_video,
                    checkHandler: function(item, checked) {
                        Frog.Prefs.set('include_video', checked);
                        item.parentMenu.hide();
                        self.fireEvent('onChange', [Frog.Prefs]);
                    }
                }
                
            ]
        });

        return menu;
    },
    switchArtistCallback: function(name) {
        var selected = $$('.thumbnail.selected');
        guids = [];
        selected.each(function(item) {
            guids.push(item.dataset.frog_guid);
        });
        new Request.JSON({
            url: '/frog/switchartist',
            headers: {"X-CSRFToken": Cookie.read('csrftoken')},
            //async: false,
            onSuccess: function(res) {
                if (res.isSuccess) {
                    selected.each(function(el) {
                        var tag = el.getElement('.frog-tag');
                        tag.set('text', res.value.name.capitalize());
                        tag.dataset.frog_tag_id = res.value.tag;
                    });
                }
            }
        }).POST({'artist': name.toLowerCase(), guids: guids.join(',')});
        selected.each(function(el) {
            var tag = el.getElement('.frog-tag');
            tag.set('text', name.capitalize());
            tag.dataset.frog_tag_id = Frog.Tags.get(name.toLowerCase());
        });
    },
    getNavMenu: function(menu) {
        var grid = Ext.create('Ext.grid.Panel', {
            //renderTo: menu,
            width: 600,
            height: 300,
            frame: true,
            title: 'Galleries',
            store: this.galleryStore,
            iconCls: 'icon-user',
            columns: [{
                text: 'Title',
                flex: 2,
                sortable: true,
                dataIndex: 'title'
            }, {
                text: 'Images',
                flex: 1,
                sortable: true,
                dataIndex: 'image_count',
                field: {
                    xtype: 'textfield'
                }
            }, {
                text: 'Videos',
                flex: 1,
                sortable: true,
                dataIndex: 'video_count',
                field: {
                    xtype: 'textfield'
                }
            }, {
                text: 'Description',
                flex: 2,
                dataIndex: 'description'
            }]
        });
        grid.on('itemClick', function(view, rec, item) {
            location.href = '/frog/gallery/' + rec.data.id;
        });

        return grid;
    }
})