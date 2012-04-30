

Frog.QueryBuilder = new Class({
    Implements: [Options, Events],
    options: {
        data: [],
        onChange: function(){}
    },
    initialize: function(options) {
        var self = this;
        this.setOptions(options);

        this.data = this.options.data;
        this.element = new Element('div');

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
        var input = new Element('input').inject(li);
        var completer = new Meio.Autocomplete(input, '/frog/tag/search', {
            filter: {
                path: 'name'
            },
            urlOptions: {
                extraParams: [{
                    name: 'search', value: true
                }]
            },
            onSelect: function(elements, value) {
                var tag, name;
                if (value.id > 0) {
                    self.data[idx].push(value.id);
                    name = value.name;
                }
                else {
                    self.data[idx].push(this.inputedText);
                    name = this.inputedText;
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
                ul.grab($(tag), 'top');
                elements.field.node.value = "";
                self.fireEvent('onChange', [self.data]);
            }
        });
        li.inject(ul);

    },
    removeBucket: function(idx) {

    }
})