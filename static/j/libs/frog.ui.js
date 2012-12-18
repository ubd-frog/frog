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
    var ID, Store, ToolBar;
    var navmenu = Ext.create('Ext.menu.Menu');
    var managemenu =  Ext.create('Ext.menu.Menu');
    var uploadEnabled = false;
    var advancedFilter = Frog.Prefs.advanced_filter;


    // -- Models
    Ext.define('Gallery', {
        extend: 'Ext.data.Model',
        fields: [
            {name: 'id'},
            {name: 'title'},
            {name: 'image_count', type: 'int'},
            {name: 'video_count', type: 'int'},
            {name: 'owner'},
            {name: 'description'}
        ]
    });
    Store = Ext.create('Ext.data.Store', {
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

    ToolBar = Ext.create('Ext.toolbar.Toolbar');
    RemoveObserver = new Frog.Observer();
    ChangeObserver = new Frog.Observer();
    FilterObserver = new Frog.Observer();

    function setId(id) {
        ID = id;
    }

    function enableUploads() {
        uploadEnabled = true;
    }

    function render(el) {
        var menuremove, menucopy, menudownload, menuswitchartist;
        ToolBar.render(el);
        // -- Navigation panel
        navmenu.add(buildNav());
        ToolBar.add({
            text: 'Navigation',
            icon: Frog.icon('compass'),
            menu: navmenu
        });
        // -- Check for user
        new Request.JSON({
            url: '/frog/getuser',
            async: false,
            onSuccess: function(res) {
                if (res.isSuccess) {
                    if (uploadEnabled) {
                        // -- Upload button
                        ToolBar.add({
                            id: 'frogBrowseButton',
                            text: 'Upload',
                            icon: Frog.icon('add')
                        });
                    }
                    // -- Edit Tags button
                    ToolBar.add({
                        text: 'Edit Tags',
                        icon: Frog.icon('tag_orange'),
                        handler: editTagsHandler
                    });
                    // Manage Menu
                    menuremove = Ext.create('Ext.menu.Item', {
                        text: 'Remove Selected',
                        icon: Frog.icon('cross'),
                        handler: removeHandler
                    });
                    menucopy = Ext.create('Ext.menu.Item', {
                        text: 'Copy to Gallery',
                        icon: Frog.icon('page_white_copy'),
                        handler: copyHandler
                    });
                    menudownload = Ext.create('Ext.menu.Item', {
                        text: 'Download Sources',
                        icon: Frog.icon('compress'),
                        handler: downloadHandler
                    });
                    menuswitchartist = Ext.create('Ext.menu.Item', {
                        text: 'Switch Artist',
                        icon: Frog.icon('user_edit'),
                        handler: switchArtistHandler
                    });
                    managemenu.add([menuremove, menucopy, menudownload, '-', menuswitchartist]);
                    ToolBar.add({
                        text: 'Manage',
                        icon: Frog.icon('photos'),
                        menu: managemenu
                    });
                    ToolBar.add({
                        text: 'Filter',
                        icon: Frog.icon('filter'),
                        enableToggle: true,
                        pressed: advancedFilter,
                        toggleHandler: function(btn) {
                            advancedFilter = btn.pressed;
                            Frog.Prefs.set('advanced_filter', advancedFilter);
                            FilterObserver.fire(advancedFilter);
                        }
                    });
                    ToolBar.add('-');
                    
                    // -- Help button
                    ToolBar.add({
                        icon: Frog.icon('help'),
                        handler: helpHandler
                    });
                    // -- Preferences Menu
                    ToolBar.add({
                        icon: Frog.icon('cog'),
                        menu: buildPrefMenu()
                    });
                }
            }
        }).GET();
        
        // -- RSS button
        ToolBar.add({
            icon: Frog.icon('feed'),
            handler: rssHandler
        });
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
    function buildNav() {
        var grid = Ext.create('Ext.grid.Panel', {
            width: 600,
            height: 300,
            frame: true,
            title: 'Galleries',
            store: Store,
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
    function buildPrefMenu() {
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
            ChangeObserver.fire(Frog.Prefs);
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
                        ChangeObserver.fire(Frog.Prefs);;
                    }
                }, {
                    xtype: 'menucheckitem',
                    text: 'Incude Video',
                    checked: Frog.Prefs.include_video,
                    checkHandler: function(item, checked) {
                        Frog.Prefs.set('include_video', checked);
                        item.parentMenu.hide();
                        ChangeObserver.fire(Frog.Prefs);;
                    }
                }
                
            ]
        });

        return menu;
    }
    function editTagsHandler() {
        var guids = [];
        $$('.selected').each(function(item) {
            guids.push(item.dataset.frog_guid);
        });
        var win = Ext.create('widget.window', {
            title: 'Edit Tags',
            icon: Frog.icon('tag_orange'),
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
    function removeHandler(silent) {
        if (typeof(silent) === 'undefined') {
            silent = false;
        }
        else if (typeof(silent) !== 'boolean') {
            silent = false;
        }
        
        var ids = [];
        $$('.selected').each(function(item) {
            ids.push(item.dataset.frog_tn_id.toInt());
        });
        RemoveObserver.fire({ids: ids, silent: silent});
    }
    function copyHandler() {
        var win = Ext.create('widget.window', {
            title: 'Copy to Gallery',
            icon: Frog.icon('page_white_copy'),
            closable: true,
            resizable: false,
            modal: true,
            width: 600,
            height: 330,
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
                        store: Store,
                        displayField: 'title',
                        valueField: 'id',
                        id: 'frog_gallery_id'
                    }
                ]
            }, {
                xtype: 'checkbox',
                fieldLabel: 'Move Items?',
                name: 'move'
            }],
            buttons: [{
                text: 'Submit',
                handler: function() {
                    var data = fp.getForm().getValues();
                    var selected = $$('.thumbnail.selected');
                    var obj = {};

                    data.id = data['frog_gallery_id-inputEl'];
                    if (typeof(data.id) === 'undefined') {
                        Ext.MessageBox.show({
                            title: 'Missing Information',
                            msg: 'Please enter a title or choose an existing gallery',
                            buttons: Ext.MessageBox.OK,
                            icon: Ext.MessageBoxINFO
                        });
                        
                        return false;
                    }

                    // -- New Gallery
                    if (data.title !== "") {
                        // -- Create the new gallery first synchronously
                        var private = (data.private === 'on') ? true : false;
                        new Request.JSON({
                            url: '/frog/gallery',
                            async: false,
                            onSuccess: function(res) {
                                data.id = res.value.id;
                            }
                        }).POST({title: data.title, description: data.description, private: private});
                    }

                    guids = [];
                    selected.each(function(item) {
                        guids.push(item.dataset.frog_guid);
                    });
                    obj.guids = guids.join(',');

                    if (data.move === 'on' && data.id !== ID) {
                        obj.move = ID;
                    }

                    new Request.JSON({
                        url: '/frog/gallery/' + data.id,
                        emulation: false,
                        async: false,
                        onSuccess: function(res) {
                            Store.sync();
                            Ext.MessageBox.confirm('Confirm', 'Would you like to visit this gallery now?', function(res) {
                                if (res === 'yes') {
                                    window.location = '/frog/gallery/' + data.id;
                                }
                            });
                        }
                    }).PUT(obj);
                    win.close();

                    if (typeof(obj.move) !== 'undefined') {
                        removeHandler(true);
                    }
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
    function downloadHandler() {
        var selected = $$('.thumbnail.selected');
        guids = [];
        selected.each(function(item) {
            guids.push(item.dataset.frog_guid);
        });
        location.href = '/frog/download?guids=' + guids.join(',');
    }
    function switchArtistHandler() {
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
        var input = new Element('input', {autofocus: 'autofocus', placeholder: "Search"});

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
                    switchArtistCallback(input.value);
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
    function rssHandler() {
        var win = Ext.create('widget.window', {
            title: 'RSS Feeds',
            icon: Frog.icon('feed'),
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
                text: "Select a feed frequency you'd like to subscribe to and the images will be available through Outlook",
                height: 100
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
                    location.href = 'feed://' + location.host + '/frog/rss/' + ID + '/' + r;
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
    function helpHandler() {
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
            bodyStyle: 'padding: 5px; background: transparent;'
        });
        win.show();
        win.add({
            xtype: 'label',
            text: "Have a question, problem or suggestion?",
            style: {
                'font-size': '14px',
                'font-weight': 'bold'
            }
        })
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
        win.add(fp)
    }
    function addPrivateMenu() {
        var id = this.id;
        var item = managemenu.add({
            text: 'Make public',
            icon: Frog.icon('world'),
            handler: function() {
                Ext.MessageBox.confirm('Confirm', 'Are you sure you want to make this public?', function(res) {
                    if (res === 'yes') {
                        new Request.JSON({
                            url: '/frog/gallery/' + ID,
                            emulation: false,
                            headers: {"X-CSRFToken": Cookie.read('csrftoken')}
                        }).PUT({private: false});
                        managemenu.remove(item);
                    }
                });
            }
        });
    }
    function switchArtistCallback(name) {
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
    }

    

    // -- API
    var api = {
        render: render,
        setId: setId,
        toolbar: ToolBar,
        addEvent: addEvent,
        addTool: addTool,
        enableUploads: enableUploads,
        addPrivateMenu: addPrivateMenu,
        isAdvancedFilterEnabled: function() { return advancedFilter; }
    };

    return api;

})(window.Frog);