

Frog.TagManager = new Class({
    initialize: function() {
        new Request.JSON({
            url: '/frog/tag/',
            onSuccess: function(res) {
                if (res.isSuccess) {
                    Frog.Tags = {};
                    res.values.each(function(tag) {
                        Frog.Tags[tag.id] = tag.name;
                    });
                }
                else if (res.isError) {
                    throw res.message;
                }
            }
        }).GET({json:true});
    },
    get: function(arg) {
        var value;
        if (typeOf(arg) === 'number') {
            value = Frog.Tags[arg];
        }
        else {
            var idx = Frog.Tags.values().indexOf(arg);
            if (idx >= 0) {
                value = Frog.Tags.keys()[idx];
            }
            else {
                new Request.JSON({
                    url: '/frog/tag/',
                    async: false,
                    onSuccess: function(res) {
                        if (res.isSuccess) {
                            value = res.value.id;
                        }
                    }
                }).POST({name: arg});
            }
        }
        
        return value;
    },
    getByName: function(name) {

    },
    getByID: function(id) {

    }
})