/*
Copyright (c) 2016 Brett Dixon

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

Frog.Tour = (function() {
    function start(name) {
        var gallery = {
            id: "gallery",
            steps: [
                {
                    title: "Search",
                    content: "Here you can search by text or tags.  Just start typing and see what tags are available.",
                    target: document.querySelector(".frog-bucket li input"),
                    placement: "right",
                    yOffset: -20
                },
                {
                    title: "Thumbnail",
                    content: "Hover over the thumbnail.<br />Each thumbnail contains the artist name and the image title.  Click it to view the image.  You can also...",
                    target: document.querySelector('.thumbnail:nth-child(3)'),
                    placement: "right",
                    xOffset: -10
                },
                {
                    title: "Likes &amp; Comments",
                    content: "Like the image or comment on it",
                    target: document.querySelector('.thumbnail:nth-child(3) .frog-comment-bubble'),
                    placement: "right",
                    yOffset: -20
                },
                {
                    title: "Navigation Menu",
                    content: "From here you can view other galleries including your personal gallery",
                    target: document.querySelector('#button-1018'),
                    placement: "bottom"
                },
                {
                    title: "Upload",
                    content: "Click to browse or simply drag files into the site.  At least one tag is required when you upload content",
                    target: document.querySelector('#frogBrowseButton'),
                    placement: "bottom"
                },
                {
                    title: "Edit Tags",
                    content: "This will open a window that shows all tags on the selected items.  Drag left or right to add or remove tags from the selected items.",
                    target: document.querySelector('#button-1020'),
                    placement: "bottom"
                },
                {
                    title: "Manage Menu",
                    content: "This menu contains management commands like removing items or copying them to another gallery",
                    target: document.querySelector('#button-1027'),
                    placement: "bottom"
                },
                {
                    title: "Advanced Filter",
                    content: "This enables advanced filtering which allows you to create more complex queries.  For example, get all items from Bill and Bob that are also tagged with \"foo\"",
                    target: document.querySelector('#button-1028'),
                    placement: "bottom"
                },
                {
                    title: "Selection",
                    content: "One last thing about selection.  Simply hold down CTRL and you can drag to select items or click to select individual items.",
                    target: document.querySelector('#gallery'),
                    placement: "top",
                    xOffset: "center",
                    yOffset: 300
                }
            ],
            onEnd: function() {
                Frog.Prefs.set('tourGallery', true);
            }
        };
        var viewer = {
            id: "viewer",
            steps: [
                {
                    title: "Title",
                    content: "Double click to edit the title",
                    target: document.querySelector("#frog_viewer_info h1"),
                    placement: "right",
                    yOffset: -20
                },
                {
                    title: "Description",
                    content: "Double click to edit the description",
                    target: document.querySelector("#frog_viewer_info pre"),
                    placement: "right",
                    yOffset: -20
                }
            ],
            onEnd: function() {
                Frog.Prefs.set('tourViewer', true);
            }
        };
        
        var tour;
        if (name === "gallery") {
            tour = gallery;
        }
        else if (name === "viewer") {
            tour = viewer;
        }
        
        hopscotch.startTour(tour);
    }

    return start;
})();
