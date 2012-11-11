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


Frog.Uploader = new Class({
    Implements: Events,
    initialize: function(id) {
        var self = this;
        this.id = id;
        this.element = new Element('div', {'id': 'frog_upload'}).inject(document.body, 'top');
        var list = new Element('div', {'id': 'frog_upload_files'}).inject(this.element);
        var uploader = new plupload.Uploader({
            runtimes: 'html5',
            browse_button: 'frogBrowseButton',
            drop_element: 'frog_upload',
            container: 'frog_upload',
            max_file_size: '500mb',
            url: '/frog/',
            headers: {"X-CSRFToken": Cookie.read('csrftoken')},
            multipart_params: {
                'galleries': this.id.toString()
            },
            filters: [
                {title: "Image files", extensions: "jpg,png,tif,tiff"},
                {title: "Video files", extensions: "mp4,avi,mov,wmv"}
            ]
        });

        uploader.init();

        uploader.bind('FilesAdded', function(up, files) {
            if (!self.element.isVisible()) {
                self.element.show();
                self.setupUI();
                self.uploaderList.show();
            }
            files.each(function(f) {
                new Request.JSON({
                    url: '/frog/isunique',
                    onSuccess: function(res) {
                        obj = {
                            id: f.id,
                            file: f.name,
                            size: f.size,
                            percent: 0,
                            unique: res.value === true
                        }
                        if (obj.unique) {
                            obj.date = Date.now();
                        }
                        else {
                            obj.date = new Date(res.value.created);
                        }
                        var item = self.uploaderList.store.add(obj);
                    }
                }).GET({path:f.name})
            });
        });

        uploader.bind('UploadProgress', function(up, file) {
            var row = self.uploaderList.store.getById(file.id);
            if (row) {
                row.set('percent', file.percent);
            }
        });

        uploader.bind('FileUploaded', function(up, file, res) {
            var index = self.uploaderList.store.getById(file.id)
            self.uploaderList.store.remove(index);
        });

        uploader.bind('UploadComplete', function(up, files) {
            self.element.hide();
            self.uploaderList.store.removeAll();
            self.uploaderList.hide();
            self.fireEvent('onComplete', [this]);
        });

        this.uploader = uploader;

        document.body.addEventListener('dragenter', function(e) {
            if (!e.dataTransfer.types.contains('text/html')) {
                self.element.show();
                self.setupUI();
                self.uploaderList.show();
            }
        }, false);
    },
    toElement: function() {
        return this.element;
    },
    setupUI: function() {
        var self = this;
        if (this.uploaderList) {
            return this.uploaderList;
        }
        
        var store = Ext.create('Ext.data.ArrayStore', {
            fields: [
                {name: 'id'},
                {name: 'file'},
                {name: 'size', type: 'int'},
                {name: 'percent', type: 'int'},
                {name: 'unique', type: 'bool'},
                {name: 'date', type: 'date'}
            ]
        });
        var grid = Ext.create('Ext.grid.Panel', {
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
                    text: 'Created',
                    flex: 2,
                    sortable: false,
                    dataIndex: 'date',
                    xtype: 'datecolumn',
                    format:'Y-m-d'
                },
                {
                    text     : '%',
                    flex     : 1,
                    sortable : false,
                    dataIndex: 'percent'
                },
                {
                    xtype: 'actioncolumn',
                    flex: 1,
                    sortable: false,
                    items: [
                        {
                            text: 'remove',
                            icon: '/static/frog/i/delete.png',
                            handler: function(grid, rowIndex, colIndex) {
                                var rec = store.getAt(rowIndex);
                                var file = self.uploader.getFile(rec.get('id'));
                                self.uploader.removeFile(file);
                                store.remove([rec]);
                            }
                        }
                    ]
                }
            ],
            height: 350,
            width: '100%',
            title: 'Files to Upload',
            renderTo: 'frog_upload_files',
            viewConfig: {
                stripeRows: true,
                getRowClass: function(record) {
                    var c = record.get('unique');
                    return (c) ? '' : 'red';
                }
            }
        });

        var uploadButton = Ext.create('Ext.Button', {
            text: 'Upload Files',
            renderTo: 'frog_upload_files',
            scale: 'large',
            handler: function() {
                self.uploader.start();
            }
        });
        var uploadButton = Ext.create('Ext.Button', {
            text: 'Cancel',
            renderTo: 'frog_upload_files',
            scale: 'large',
            handler: function() {
                self.element.hide();
                self.uploaderList.store.removeAll();
                self.uploaderList.hide();
            }
        });

        this.uploaderList = grid;
    },
})