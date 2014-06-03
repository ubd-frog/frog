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