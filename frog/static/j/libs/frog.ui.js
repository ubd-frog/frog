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


Frog.UI = (function(Frog) {
    var self = this;
    var ID, Store, ToolBar;
    var navmenu = Ext.create('Ext.menu.Menu');
    
    var uploadEnabled = false;
    var advancedFilter = Frog.Prefs.advanced_filter;

    self.renderCallback = null;
    Ext.tip.QuickTipManager.init();


    // -- Models
    Ext.define('Gallery', {
        extend: 'Ext.data.Model',
        fields: [
            {name: 'id'},
            {name: 'title'},
            {name: 'owner'},
            {name: 'description'}
        ]
    });
    Ext.define('Artist', {
        extend: 'Ext.data.Model',
        fields: ['id', 'name', 'username', 'email']
    });
    Store = Ext.create('Ext.data.TreeStore', {
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
    var GalleryStore = Ext.create('Ext.data.Store', {
        autoLoad: true,
        autoSync: true,
        model: 'Gallery',
        storeId: 'galleries',
        proxy: {
            type: 'ajax',
            url: '/frog/gallery?flat=1',
            reader: {
                type: 'json',
                root: 'values'
            }
        }
    });
    Ext.create('Ext.data.Store', {
        storeId: 'security',
        fields: ['name', 'value'],
        data: [
            {name: 'Public', value: 0},
            {name: 'Private', value: 1},
            {name: 'Personal', value: 2}
        ]
    });
    Ext.create('Ext.data.Store', {
        model: 'Artist',
        storeId: 'artists',
        proxy: {
            type: 'ajax',
            url: '/frog/artistlookup',
            reader: {
                type: 'json',
                root: 'values'
            }
        },
        autoLoad: true
    });

    ToolBar = Ext.create('Ext.toolbar.Toolbar');
    var RemoveObserver = new Frog.Observer();
    var ChangeObserver = new Frog.Observer();
    var FilterObserver = new Frog.Observer();

    function setId(id) {
        ID = id;
    }

    function enableUploads() {
        uploadEnabled = true;
    }

    function render(el) {
        ToolBar.render(el);
        GalleryStore.on('load', function() {
            navmenu.removeAll();
            navmenu.add({
                text: 'Create Gallery',
                icon: Frog.icon('add'),
                handler: createHandler
            });
            navmenu.add('-');
            for (var i=0;i<this.getCount();++i) {
                var item = this.getAt(i);
                var icon = (Frog.GalleryObject.id === item.get('id')) ? Frog.icon('tick') : null;
                navmenu.add({
                    text: this.getAt(i).get('title'),
                    icon: icon,
                    href: '/frog/gallery/' + item.get('id')
                });
            }
        });
        ToolBar.add({
            text: 'Galleries',
            icon: Frog.icon('photos'),
            tooltip: 'Switch to different galleries you have access to',
            menu: navmenu
        });
        // -- Check for user
        new Request.JSON({
            url: '/frog/getuser',
            onSuccess: function(res) {
                if (res.isError) {
                    addLoginAction();
                }
                else{
                    if (uploadEnabled) {
                        // -- Upload button
                        ToolBar.add({
                            id: 'frogBrowseButton',
                            text: 'Upload',
                            icon: Frog.icon('add'),
                            tooltip: 'Browse for files to upload or drag them into the browser'
                        });
                    }
                    // -- Edit Tags button
                    ToolBar.add({
                        text: 'Tags',
                        icon: Frog.icon('tag_orange'),
                        tooltip: 'Add or remove tags from selected items',
                        handler: editTagsHandler
                    });
                    var menuconfig = {
                        hideMode: 'display',
                        items: [
                            {
                                text: 'Remove Items',
                                icon: Frog.icon('cross'),
                                handler: removeHandler
                            },
                            {
                                text: 'Copy',
                                icon: Frog.icon('page_white_copy'),
                                handler: Frog.copy
                            },
                            {
                                text: 'Cut',
                                icon: Frog.icon('cut'),
                                handler: Frog.cut
                            },
                            {
                                text: 'Paste',
                                icon: Frog.icon('page_white_paste'),
                                disabled: window.localStorage.getItem('clipboard') === null,
                                handler: Frog.paste
                            },
                            '-',
                            {
                                text: 'Download Sources',
                                icon: Frog.icon('compress'),
                                handler: downloadHandler
                            },
                            {
                                text: 'Switch Artist',
                                icon: Frog.icon('user_edit'),
                                handler: switchArtistHandler
                            }
                        ]
                    };
                    if (res.value.gallery !== null) {
                        menuconfig.items.push('-');
                        menuconfig.items.push(
                            {
                                text: 'Security',
                                icon: Frog.icon('lock'),
                                menu: {
                                    items: [
                                        {
                                            text: 'Public',
                                            group: 'security',
                                            checked: res.value.gallery.security === 0,
                                            handler: securityHandler
                                        },
                                        {
                                            text: 'Private',
                                            group: 'security',
                                            checked: res.value.gallery.security === 1,
                                            handler: securityHandler
                                        },
                                        {
                                            text: 'Personal',
                                            group: 'security',
                                            checked: res.value.gallery.security === 2,
                                            handler: securityHandler
                                        }
                                    ]
                                }
                            }
                        );
                    }
                    var managemenu =  Ext.create('Ext.menu.Menu', menuconfig);
                    
                    ToolBar.add({
                        text: 'Manage',
                        icon: Frog.icon('photos'),
                        menu: managemenu
                    });
                    ToolBar.add({
                        text: 'Filter',
                        icon: Frog.icon('filter'),
                        tooltip: 'Toggle between normal and advanced filtering',
                        enableToggle: true,
                        pressed: advancedFilter,
                        toggleHandler: function(btn) {
                            advancedFilter = btn.pressed;
                            btn.setText((advancedFilter) ? 'Advanced Filter' : 'Filter');
                            Frog.Prefs.set('advanced_filter', advancedFilter);
                            FilterObserver.fire(advancedFilter);
                            if (advancedFilter) {
                                msg('You are now using the Advanced Filter', 'alert-info');
                            }
                            else {
                                msg('You are now using the Standard Filter', 'alert-success');
                            }
                        }
                    });
                    ToolBar.add('-');
                    // -- Preferences Menu
                    ToolBar.add({
                        text: 'Preferences',
                        icon: Frog.icon('cog'),
                        menu: buildPrefMenu()
                    });
                    ToolBar.add('-');
                    // -- Help button
                    ToolBar.add({
                        text: 'Help',
                        icon: Frog.icon('help'),
                        handler: helpHandler
                    });
                    ToolBar.add({
                        text: "Documentation",
                        icon: Frog.icon("book"),
                        href: "http://frog.readthedocs.io/en/latest/index.html#user-guide"
                    })
                }
        
                if (self.renderCallback !== null) {
                    renderCallback();
                }
            }
        }).GET({gallery: ID});
    }
    function addEvent(event, fn) {
        switch(event) {
            case 'remove':
                RemoveObserver.subscribe(fn);
                break;
            case 'change':
                ChangeObserver.subscribe(fn);
                break;
            case 'filter':
                FilterObserver.subscribe(fn);
                break;
            case 'render':
                self.renderCallback = fn;
                break;
        }
    }
    function addTool(label, icon, callback) {
        ToolBar.add('-');
        ToolBar.add({
            text: label,
            icon: icon,
            handler: callback
        });
    }

    // Private
    function buildPrefMenu() {
        var colorMenu = Ext.create('Ext.menu.ColorPicker', {
            height: 24,
            hideOnClick: true,
            handler: function(cm, color){
                Frog.Prefs.set('backgroundColor', JSON.stringify('#' + color));
            }
        });
        colorMenu.picker.colors = ['000000', '424242', '999999', 'FFFFFF'];
        var tileSizeHandler = function(item, checked) {
            Frog.Prefs.set('tileCount', item.value, ChangeObserver.fire.bind(ChangeObserver));
        };
        var batchSize = Ext.create('Ext.form.field.Number', {
            value: Frog.Prefs.batchSize,
            minValue: 0,
            maxValue: 500
        });
        batchSize.on('change', function(field, val) { 
            Frog.Prefs.set('batchSize', val);
        });

        var prefmenu = Ext.create('Ext.menu.Menu', {
            hideMode: 'display',
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
                            hideOnClick: true,
                            checkHandler: tileSizeHandler
                        }, {
                            text: 'Medium (9)',
                            value: 9,
                            hideOnClick: true,
                            checked: Frog.Prefs.tileCount === 9,
                            group: 'theme',
                            checkHandler: tileSizeHandler
                        }, {
                            text: 'Small (12)',
                            value: 12,
                            checked: Frog.Prefs.tileCount === 12,
                            hideOnClick: true,
                            group: 'theme',
                            checkHandler: tileSizeHandler
                        }
                    ]
                },
                {
                    xtype: 'menucheckitem',
                    text: "Always Show Thumbnail Info",
                    checked: Frog.Prefs.semi_transparent,
                    hideOnClick: true,
                    checkHandler: function(item, checked) {
                        Frog.Prefs.set('semi_transparent', checked, function() {
                            if (checked) {
                                $$('.tag-hover').addClass('tag-hover-semi');
                            }
                            else {
                                $$('.tag-hover').removeClass('tag-hover-semi');
                            }
                        });
                    }
                }
            ]
        });

        return prefmenu;
    }
    function editTagsHandler() {
        var guids = [];
        $$('.selected').each(function(item) {
            var guid = Frog.util.getData(item, 'frog_guid');
            guids.push(guid);
        });

        if (guids.length === 0) {
            Ext.MessageBox.show({
                title: 'Selection Error',
                msg: 'Please select at least one item to mange tags for',
                buttons: Ext.MessageBox.OK
            });
            return;
        }

        var win = Ext.create('widget.window', {
            title: 'Tags',
            icon: Frog.icon('tag_orange'),
            closable: true,
            modal: true,
            width: 800,
            height: 650,
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
                        var id = Frog.util.getData(item, 'frog_tag_id');
                        add.push(id);
                    });
                    $$('#frog_rem li').each(function(item) {
                        var id = Frog.util.getData(item, 'frog_tag_id');
                        rem.push(id);
                    });
                    
                    new Request.JSON({
                        url: '/frog/tag/manage',
                        headers: {"X-CSRFToken": Cookie.read('csrftoken')},
                        onSuccess: function(res) {
                            res.values.each(function(item) {
                                item.tags.each(function(tag) {
                                    Frog.Tags.tags[tag.id] = tag.name.toLowerCase();
                                });
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
    function removeHandler(silent) {
        if (typeof(silent) === 'undefined') {
            silent = false;
        }
        else if (typeof(silent) !== 'boolean') {
            silent = false;
        }
        
        var ids = [];
        $$('.selected').each(function(item) {
            ids.push(Frog.util.getData(item, 'frog_tn_id').toInt());
        });
        RemoveObserver.fire({ids: ids, silent: silent});
    }
    function createHandler() {
        var form = Ext.create('Ext.form.Panel', {
            items: [
                {
                    fieldLabel: 'Title',
                    xtype: 'textfield',
                    name: 'title'

                }, {
                    fieldLabel: 'Description',
                    xtype: 'textareafield',
                    name: 'description'
                }, {
                    fieldLabel: 'Security Level',
                    xtype: 'combobox',
                    name: 'security',
                    editable: false,
                    store: 'security',
                    displayField: 'name',
                    valueField: 'value',
                    value: 0
                }
            ],
            buttons: [{
                text: 'Submit',
                handler: function() {
                    var data = form.getForm().getValues();
                    var selected = $$('.thumbnail.selected');

                    if (data.title === '') {
                        Ext.MessageBox.show({
                            title: 'Missing Information',
                            msg: 'Please enter a title',
                            buttons: Ext.MessageBox.OK,
                            icon: Ext.MessageBoxINFO
                        });

                        return false;
                    }

                    new Request.JSON({
                        url: '/frog/gallery',
                        async: false,
                        headers: {"X-CSRFToken": Cookie.read('csrftoken')},
                        onSuccess: function(res) {
                            msg('Gallery "' + res.value.title + '" added successfully', 'alert-success');
                            data.id = res.value.id;
                            navmenu.add({
                                text: res.value.title,
                                href: '/frog/gallery/' + res.value.id
                            });
                        }
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
        var win = Ext.create('widget.window', {
            title: 'Create Gallery',
            icon: Frog.icon('photos'),
            closable: true,
            resizable: false,
            modal: true,
            bodyStyle: 'padding: 5px;',
            width: 400,
            items: [form]
        });
        win.show();
    }
    function downloadHandler() {
        var selected = $$('.thumbnail.selected');
        guids = [];
        selected.each(function(item) {
            guids.push(Frog.util.getData(item, 'frog_guid'));
        });
        location.href = '/frog/download?guids=' + guids.join(',');
    }
    function switchArtistHandler() {
        var win = Frog.UI.SwitchArtist();
        win.show();
    }
    function helpHandler() {
        var fp = Ext.create('Ext.FormPanel', {
            items: [
            {
                xtype: 'textareafield',
                name: 'message',
                anchor: '100%',
                height: 300
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
        var win = Ext.create('widget.window', {
            title: 'Ask for Help',
            icon: Frog.icon('help'),
            closable: true,
            closeAction: 'hide',
            resizable: false,
            modal: true,
            width: 600,
            height: 400,
            bodyPadding: 10,
            bodyStyle: 'padding: 5px; background: transparent;',
            items: [
                {
                    xtype: 'label',
                    text: "Have a question, problem or suggestion?",
                    style: {
                        'font-size': '14px',
                        'font-weight': 'bold'
                    }
                },
                fp
            ]
        });
        win.show();
    }
    function securityHandler(item, event) {
        var store = Ext.getStore('security');
        new Request.JSON({
            url: '/frog/gallery/' + ID,
            emulation: false,
            headers: {"X-CSRFToken": Cookie.read('csrftoken')}
        }).PUT({security: store.findRecord('name', item.text).data.value});
    }

    function addLoginAction() {
        ToolBar.add('-');
        ToolBar.add({
            text: 'Login',
            icon: Frog.icon('user'),
            handler: function() {
                location.href = '/frog';
            }
        });
    }

    function createBox(text, cls){
       return '<div class="msg ' + cls + '"><p>' + text + '</p></div>';
    }
    var msgCt;
    function msg(text, cls){
        if (!msgCt) {
            msgCt = Ext.core.DomHelper.insertFirst(document.body, {id:'msg-div'}, true);
        }
        var s = Ext.String.format.apply(String, Array.prototype.slice.call(arguments, 1));
        var m = Ext.core.DomHelper.append(msgCt, createBox(text, cls), true);
        m.hide();
        m.slideIn('t').ghost("t", { delay: 1000, remove: true});
    }

    // -- API
    var api = {
        render: render,
        setId: setId,
        toolbar: ToolBar,
        addEvent: addEvent,
        addTool: addTool,
        enableUploads: enableUploads,
        isAdvancedFilterEnabled: function() { return advancedFilter; },
        editTags: editTagsHandler,
        alert: msg
    };

    return api;

})(window.Frog);


Frog.UI.SwitchArtist = function() {
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

    function switchArtistCallback(name) {
        var selected = $$('.thumbnail.selected');
        var guids = [];
        selected.each(function(item) {
            guids.push(Frog.util.getData(item, 'frog_guid'));
        });
        new Request.JSON({
            url: '/frog/switchartist',
            headers: {"X-CSRFToken": Cookie.read('csrftoken')},
            onSuccess: function(res) {
                if (res.isError) {
                    Frog.UI.alert('An error occurred, artist was not switched', 'alert-danger');
                }
                else {
                    Frog.UI.alert('Artist successfully switched', 'alert-success');
                    selected.each(function(el) {
                        var tag = el.getElement('span + div a.frog-tag');
                        tag.set('text', res.value.name.capitalize());
                        Frog.util.setData(tag, 'frog_tag_id', res.value.tag);
                    });
                }
            }
        }).POST({'artist': name.toLowerCase(), guids: guids.join(',')});
        selected.each(function(el) {
            var tag = el.getElement('span + div a.frog-tag');
            tag.set('text', name.capitalize());
            Frog.util.getData(tag, 'frog_tag_id', Frog.Tags.get(name.toLowerCase()));
        });
    }

    var fp = Ext.create('Ext.FormPanel', {
        items: [{
            xtype: 'label',
            text: "Start typing the name of an artist or if this is a new artist, type in the first and last name and click Send"
        }, {
            xtype: 'combobox',
            fieldLabel: 'Artist Name',
            store: 'artists',
            queryMode: 'remote',
            minChars: 2,
            displayField: 'name',
            name: 'artist_name',
            focusOnToFront: true
        }],
        buttons: [{
            text: 'Save',
            handler: function() {
                var value = this.up('form').getForm().getFieldValues();
                switchArtistCallback(value.artist_name);
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
    
    return win;
}
