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
        buckets: 3,
        onChange: function(){}
    },
    initialize: function(options) {
        var self = this;
        this.setOptions(options);

        var data = this.options.data || [[]];
        this.data = [];
        this.buckets = [];
        this.sourcebucket = null;
        this.maxBuckets = 3;
        this.__isInit = true;
        var dirty = false;

        // -- Add our main element
        this.element = new Element('div', {id: 'frog_builder'});
        var froglink = new Element('a', {href: 'https://github.com/theiviaxx/Frog'}).inject(this.element);
        var frog = new Image().inject(froglink);
        frog.addClass('frog-logo');
        frog.src = Frog.icon('frog');

        // -- Remove empty buckets
        this.clean(data);

        // -- Event bindings
        this.change = this._change.bind(this);
        this.filterHandler = this._filter.bind(this);
        Frog.UI.addEvent('filter', this.filterHandler);
        this.historyCallback = this._historyEvent.bind(this);
        window.addEventListener('hashchange', this.historyCallback, false);

        // -- Build buckets based on data
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
        if (Frog.UI.isAdvancedFilterEnabled()) {
            if (this.buckets.getLast().length() > 0) {
                this.addBucket();
            }
        }
        this.__isInit = false;

        if (dirty) {
            this.change();
        }
    },
    toElement: function() {
        return this.element;
    },
    addBucket: function() {
        var bucket = new Frog.Bucket();
        $(bucket).inject(this.element);
        bucket.addEvent('change', this.change);
        bucket.addEvent('empty', function(b) {
            if (this.buckets.length > 1) {
                b.destroy();
                this.buckets.erase(b);
                if (this.buckets.getLast().length() > 0) {
                    this.addBucket();
                }
                this.fireEvent('remove', [this, b]);
            }
        }.bind(this));
        
        this.buckets.push(bucket);

        this.fireEvent('add', this);
        
        return bucket;

    },
    addTag: function(bucket, tag_id) {
        var tag = this.buckets[bucket].addTag(tag_id);
    },
    clean: function(buckets) {
        var self = this;
        if (typeof(buckets) === 'undefined') {
            buckets = this.buckets.map(function(item) {
                return item.data();
            });
        }
        buckets.each(function(bucket) {
            var clean = bucket.filter(function(item) { return item !== "" });
            if (clean.length) {
                self.data.push(clean);
            }
        });
    },
    _historyEvent: function(e) {
        var self = this;
        if (!this.__isInit) {
            var data = Frog.util.hashData();
            this.data = data.filters;
        }
        
        this.__isInit = true;
        this.buckets.each(function(bucket) {
            bucket.destroy();
            self.fireEvent('remove', [self, bucket]);
        });
        this.buckets = [];
        this.data.each(function(bucket, idx) {
            dirty = true;
            var bucketObject = self.addBucket(true);
            bucket.each(function(t) {
                var name = (typeOf(t) === 'number') ? Frog.Tags.get(t) : t;
                var tag = new Frog.Tag(t, name);
                bucketObject.addTag(tag);
            });
        });
        if (Frog.UI.isAdvancedFilterEnabled()) {
            if (this.buckets.getLast().length() > 0) {
                this.addBucket();
            }
        }
        this.__isInit = false;
    },
    _change: function(data, bucket) {
        if (!this.__isInit) {
            var data = this.buckets.map(function(bucket) {
                return bucket.data();
            });
            if (Frog.UI.isAdvancedFilterEnabled() && typeof(bucket) !== 'undefined') {
                if (this.buckets.getLast().length() > 0 && this.buckets.length < this.options.buckets) {
                    this.addBucket();
                }
            }
            this.fireEvent('onChange', [data]);
        }
    },
    _filter: function(state) {
        var bucket;
        if (!state) {
            while(this.buckets.length > 1) {
                bucket = this.buckets.getLast();
                bucket.destroy();
                this.buckets.erase(bucket);
                this.fireEvent('remove', [this, bucket]);
            }
        }

        bucket = this.buckets[0];

        for (var i=1;i<bucket.length();i++) {
            bucket.removeTag(bucket.tags[i]);
        }
        this.change(undefined, bucket);
    },
    _enableSort: function(enable) {
        if (typeof(enable) === 'undefined') {
            enable = true;
        }

    }
});


Frog.Bucket = new Class({
    Implements: Events,
    initialize: function() {
        this.element = new Element('ul', {'class': 'frog-bucket'});
        this.li = new Element('li').inject(this.element);
        this.input = new Element('input', {placeholder: "Search"}).inject(this.li);
        this.tags = [];
        this.completer = null;

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
    length: function() {
        return this.element.childElementCount - 1;
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
            if (!Frog.UI.isAdvancedFilterEnabled()) {
                this.tags = [];
                this.element.getElements('.frog-tag').dispose();
            }
            tag.addEvent('close', this.events.tagClose);
            this.tags.push(tag);
            this.element.grab($(tag), 'top');
            this.fireEvent('onChange', [this.data(), this]);
        }

        return tag;
    },
    removeTag: function(tag) {
        for(var i=0;i<this.tags.length;i++) {
            if (tag.id === this.tags[i].id) {
                this.tags[i].close();
            }
        }
    },
    destroy: function() {
        this.element.getElements('.frog-tag').dispose();
        this.element.destroy();
        //this.completer.elements.list.node.destroy();
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
                name = this.input.value.toLowerCase().replace('search for: ', '');
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
        this.fireEvent('onChange', [this.data(), this]);
    },
    __build: function() {
        this.input.addEvent('keyup', this.events.keyUp);
        this.completer = new Meio.Autocomplete(this.input, '/frog/tag/search', {
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
            listOptions: {
                width: 300
            },
            requestOptions: {
                headers: {"X-CSRFToken": Cookie.read('csrftoken')},
            },
            onSelect: this.events.select
        });
    }
})
