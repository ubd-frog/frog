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


Frog.QueryBuilder = new Class({
    Implements: [Options, Events],
    options: {
        data: [[]],
        onChange: function(){}
    },
    initialize: function(options) {
        var self = this;
        this.setOptions(options);

        var data = this.options.data || [[]];
        this.data = [];
        this.buckets = [];
        this.sourcebucket = null;
        // this.sortables = new Sortables($$('.frog-bucket'), {
        //     clone: true,
        //     revert: true,
        //     opacity: 0.7
        // });
        // this.sortables.addEvent('start', function(el) {
        //     this.sourcebucket = el.parentNode;
        // }.bind(this));
        // this.sortables.addEvent('complete', function(el) {
        //     var bucket = el.parentNode;
        //     var id = el.dataset.frog_tag_id.toInt();
        //     if (typeOf(id) === 'null') {
        //         id = new Frog.Tag(el.dataset.frog_tag_id, el.dataset.frog_tag_id);
        //     }
        //     if (bucket !== this.sourcebucket) {
        //         this.sourcebucket
        //     }

        //     this.buckets[0].addTag(id);
        // }.bind(this));
        data.each(function(bucket) {
            var clean = bucket.filter(function(item) { return item !== "" });
            self.data.push(clean);
        })
        this.element = new Element('div', {id: 'frog_builder'});
        var frog = new Image();
        frog.addClass('frog-logo');
        frog.onload = function() {
            this.element.grab(frog);
        }.bind(this)
        frog.src = FrogStaticRoot + '/frog/i/frog.png';
        this.change = this._change.bind(this);
        this.historyCallback = this._historyEvent.bind(this);

        window.addEventListener('hashchange', this.historyCallback, false);

        var dirty = false;

        this.data.each(function(bucket, idx) {
            dirty = true;
            var bucketObject = self.addBucket(true);
            bucket.each(function(t) {
                var name = (typeOf(t) === 'number') ? Frog.Tags.get(t) : t;
                var tag = new Frog.Tag(t, name);
                bucketObject.addTag(tag);
            });
        });
        if (this.data.length === 0) {
            this.addBucket(true);
            dirty = true;
        }

        if (dirty) {
            this.change();
        }
    },
    toElement: function() {
        return this.element;
    },
    addBucket: function() {
        var idx = this.buckets.length;
        var bucket = new Frog.Bucket(idx);
        $(bucket).inject(this.element);
        bucket.addEvent('change', this.change);
        bucket.addEvent('empty', function(b) {
            if (this.buckets.length > 1) {
                $(b).destroy();
                this.buckets.erase(b);
                this.fireEvent('remove', [this, b]);
            }
        }.bind(this));
        // Ext.create('Ext.Button', {
        //     text: 'add',
        //     renderTo: bucket.li,
        //     height: 22,
        //     handler: this.addBucket.bind(this)
        // });
        
        this.buckets.push(bucket);
        //this.sortables.addLists($(bucket));

        this.fireEvent('add', this);
        
        return bucket;

    },
    addTag: function(bucket, tag_id) {
        var tag = this.buckets[bucket].addTag(tag_id);
        //this.sortables.addItems($(tag));
    },
    _historyEvent: function(e) {
        var key = (typeOf(e) === 'string') ? e : e.newURL;
        var data = JSON.parse(unescape(key.split('#')[1]));
        this.data = data.filters;
    },
    _change: function(e) {
        var data = this.buckets.map(function(bucket) {
            return bucket.data();
        });
        this.fireEvent('onChange', [data]);
        //this.sortables.addItems($$('.frog-tag'));
    }
});


Frog.Bucket = new Class({
    Implements: Events,
    initialize: function(index) {
        this.index = index;
        this.element = new Element('ul', {'class': 'frog-bucket'});
        this.element.dataset['frog_bucket_id'] = this.index;
        this.li = new Element('li').inject(this.element);
        this.input = new Element('input', {placeholder: "Search"}).inject(this.li);
        this.tags = [];

        this.events = {
            keyUp: this.keyUpEvent.bind(this),
            select: this.selectEvent.bind(this),
            tagClose: this.tagCloseEvent.bind(this)
        };

        this.__build();
    },
    toElement: function() {
        return this.element;
    },
    toString: function() {
        return this.data().toString();
    },
    data: function() {
        return this.tags.map(function(t) { return t.id; });
    },
    addTag: function(tag) {
        if (typeOf(tag) === 'number') {
            tag = new Frog.Tag(tag);
        }
        var tagIDs = this.tags.map(function(t) { return t.id; });
        if (!tagIDs.contains(tag.id)) {
            tag.addEvent('close', this.events.tagClose);
            this.tags.push(tag);
            this.element.grab($(tag), 'top');
            this.fireEvent('onChange', [this.data]);
        }

        return tag;
    },
    __build: function() {
        this.input.addEvent('keyup', this.events.keyUp);
        new Meio.Autocomplete(this.input, '/frog/tag/search', {
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
            },
            urlOptions: {
                extraParams: [{
                    name: 'search', value: true
                }]
            },
            requestOptions: {
                headers: {"X-CSRFToken": Cookie.read('csrftoken')},
            },
            onSelect: this.events.select
        });
    },
    keyUpEvent: function(e) {
        if (e.code === 13 && this.input.value !== "") {
            this.events.select(undefined, {id: 0, name: this.input.value});
        }
    },
    selectEvent: function(elements, value) {
        if (value !== "") {
            var tag, name;
            if (value.id > 0) {
                name = value.name;
                tag = new Frog.Tag(value.id, name);
            }
            else {
                name = this.input.value;
                tag = new Frog.Tag(name, name);
            }
            this.input.value = "";
            this.addTag(tag);
        }
    },
    tagCloseEvent: function(tag) {
        $(tag).destroy();
        this.tags.erase(tag);
        if (this.tags.length === 0) {
            this.fireEvent('onEmpty', [this]);
        }
        this.fireEvent('onChange');
    }
})