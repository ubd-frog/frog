

Frog.QueryBuilder = new Class({
    Implements: [Options, Events],
    options: {
        data: [],
        onChange: function(){}
    },
    initialize: function(options) {
        var self = this;
        this.setOptions(options);

        var data = this.options.data || [];
        this.data = [];
        data.each(function(bucket) {
            var clean = bucket.filter(function(item) { return item !== "" });
            self.data.push(clean);
        })
        this.element = new Element('div', {id: 'frog_builder'});

        var dirty = false;

        this.data.each(function(bucket, idx) {
            dirty = true;
            self.addBucket(true);
            bucket.each(function(t) {
                var name = (typeOf(t) === 'number') ? Frog.Tags.get(t) : t;
                var tag = new Frog.Tag(t, name);
                tag.addEvent('close', function(t) {
                    $(t).destroy();
                    if (t.id > 0) {
                        self.data[idx].erase(t.id)
                    }
                    else {
                        self.data[idx].erase(t.name)
                    }
                    self.fireEvent('onChange', [self.data]);
                })
                self.element.getChildren()[idx].grab($(tag), 'top');
            })
        })

        if (dirty) {
            this.fireEvent('onChange', [this.data]);
        }
    },
    toElement: function() {
        return this.element;
    },
    addBucket: function(silent) {
        silent = (typeOf(silent) === 'undefined') ? false : silent;
        if (!silent) {
            this.data.push([]);
        }
        var ul = new Element('ul', {'class': 'frog-bucket'}).inject(this.element);
        var self = this;
        var idx = this.data.length - 1;
        var li = new Element('li');
        var input = new Element('input', {placeholder: "Search"}).inject(li);
        input.addEvent('keyup', function(e) {
            if (e.code === 13 && this.value !== "") {
                self._selectCallback(idx, {id: 0, name: this.value}, this);
            }
        })
        var completer = new Meio.Autocomplete(input, '/frog/tag/search', {
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
            onSelect: function(elements, value) {
                if (value !== "") {
                    self._selectCallback(idx, value, elements.field.node);
                }
            }
        });
        li.inject(ul);

    },
    removeBucket: function(idx) {

    },
    addTag: function(bucket, tag_id) {
        if (!this.data[bucket]) {
            this.addBucket();
        }
        if (this.data[bucket].indexOf(tag_id) === -1) {
            this.data[bucket].push(tag_id);
            var tag = new Frog.Tag(tag_id);
            tag.addEvent('close', function(t) {
                $(t).destroy();
                if (t.id > 0) {
                    this.data[bucket].erase(t.id)
                }
                else {
                    this.data[bucket].erase(t.name)
                }
                this.fireEvent('onChange', [this.data]);
            }.bind(this))
            this.element.getChildren()[bucket].grab($(tag), 'top');
            this.fireEvent('onChange', [this.data]);
        }
    },
    _selectCallback: function(idx, value, el) {
        var tag, name;
        var self = this;
        if (value.id > 0) {
            self.data[idx].push(value.id);
            name = value.name;
        }
        else {
            self.data[idx].push(el.value);
            name = el.value;
        }
        tag = new Frog.Tag(value.id, name);
        tag.addEvent('close', function(t) {
            $(t).destroy();
            if (value.id > 0) {
                self.data[idx].erase(t.id)
            }
            else {
                self.data[idx].erase(t.name)
            }
            self.fireEvent('onChange', [self.data]);
        })
        self.element.getChildren()[idx].grab($(tag), 'top');
        el.value = "";
        self.fireEvent('onChange', [self.data]);
    }
})