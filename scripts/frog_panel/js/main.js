"use strict";


var gExtensionId = "FROG";


var FrogApp = angular.module('FrogApp', []);
FrogApp.config(['$httpProvider', function ($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
}]);
FrogApp.controller('MainController', function($scope, $q, FrogService) {
    var csInterface = new CSInterface();
    var fs = require('fs');
    var childProcess = require('child_process');

    $scope.item = {};
    $scope.thumbnail = '';
    $scope.filename = '';
    $scope.isunique = true;
    $scope.settings = FrogService.settings;
    $scope.state = 'main';
    $scope.auth = {'email': '', 'password': ''};
    $scope.message = '';
    $scope.galleries = [];
    $scope.gallery = null;

    init();

    $scope.query = function(filename) {
        $scope.filename = filename;
        FrogService.csrfPromise.then(function() {
            FrogService.isUnique(filename).then(function(res) {
                if (res.data.value === true) {
                    // -- Is Unique
                    $scope.isunique = true;
                    $scope.thumbnail = '';
                }
                else {
                    $scope.item = res.data.value;
                    $scope.thumbnail = FrogService.settings.url + res.data.value.image;
                    $scope.isunique = false;
                }
            });
        });
    };

    $scope.update = function() {
        saveWebImage($scope.filename).then(function(webimage) {
            FrogService.upload(webimage, $scope.filename).then(function() {
                fs.unlink(webimage);
                $scope.query($scope.filename);
            });
        });
    };

    $scope.changeHandler = function(gallery) {
        $scope.gallery = gallery;
        FrogService.settings.gallery = gallery;
        FrogService.writeSettings();
    };

    $scope.toggle = function() {
        $scope.state = ($scope.state == 'main') ? 'settings' : 'main';
        FrogService.getGalleries().then(function(res) {
            $scope.galleries.length = 0;
            angular.forEach(res.data.values, function (gallery, index) {
                $scope.galleries.push(gallery);
                if (gallery.id == FrogService.settings.gallery.id) {
                    $scope.gallery = $scope.galleries[index];
                }
            });
        });
    };

    $scope.view = function() {
        childProcess.spawn('cmd', ['/c', 'start', '""', FrogService.settings.url + '/v/0/' + $scope.item.guid]);
    };

    $scope.clickHandler = function() {
        FrogService.login($scope.auth.email, $scope.auth.password).then(function(result) {
            if (result.data.isError) {
                message = result.data.message;
            }
            else {
                $scope.toggle();
            }
        });
    };

    function init() {
        FrogService.readSettings();
        if (FrogService.settings.url.length == 0) {
            $scope.state = 'settings';
        }
        FrogService.csrf();
        
        FrogService.getGalleries().then(function(res) {
            $scope.galleries.length = 0;
            angular.forEach(res.data.values, function (gallery, index) {
                $scope.galleries.push(gallery);
                if (gallery.id == FrogService.settings.gallery.id) {
                    $scope.gallery = $scope.galleries[index];
                }
            });
        });
        csInterface.addEventListener("documentAfterActivate", documentChangeCallback);
        csInterface.addEventListener("documentAfterSave", documentChangeCallback);
        csInterface.evalScript('try{app.activeDocument.fullName}catch(e) {null}', function(result) {
            if (angular.isDefined(result) && result !== 'null') {
                $scope.query(result);
            }
        });
        var event = new CSEvent("com.adobe.PhotoshopPersistent", "APPLICATION");
        event.extensionId = gExtensionId;
        //csInterface.dispatchEvent(event);
    }

    function documentChangeCallback(data) {
        var result;
        var parser = new DOMParser();
        var xml = parser.parseFromString(data.data, 'text/xml');
        if (angular.isDefined(xml.children)) {
            result = xml.evaluate('//url', xml.children[0]).iterateNext();
        }
        else {
            result = xml.evaluate('//url', xml).iterateNext();
        }

        $scope.filename = '';
        $scope.thumbnail = '';
        
        if (result !== null) {
            var filename = result.textContent.split('///')[1];
            if (angular.isDefined(filename)) {
                $scope.query(filename);
            }
            $scope.$digest();
        }
    }

    function saveWebImage(filename) {
        var defer = $q.defer();
        csInterface.evalScript('saveWebImage("' + filename + '")', function (result) {
            defer.resolve(result);
        });

        return defer.promise;
    }
});

FrogApp.service('FrogService', function($http, $q) {
    var fs = require('fs');
    var path = require('path');
    var process = require('process');
    var userdir = process.env[(process.platform == 'win32') ? 'USERPROFILE' : 'HOME'];
    var settingsfile = userdir + '/frog.json';

    function factory() {
        var self = this;
        this.csrfPromise = null;
        this.settings = {
            'url': '',
            'gallery': null,
            'csrftoken': ''
        };
        this.isUnique = function(filename) {
            return $http.post(
                this.settings.url + '/frog/isunique/',
                {body: {user: process.env.USERNAME, paths: [filename]}},
                {
                    withCredentials: true
                }
            );
        };

        this.upload = function(filename, source) {
            var fd = new FormData();
            var defer = $q.defer();

            self.writeSettings();
            
            fs.readFile(filename, function(err, data) {
                var a = new Uint8Array(data);
                var b = new Blob([a], {type: 'image/png'});

                fd.append('file', b, path.basename(filename));
                fd.append('path', source);
                fd.append('user', process.env.USERNAME);
                fd.append('galleries', self.settings.gallery.id);

                $http.post(
                    self.settings.url + '/frog/',
                    fd,
                    {
                        transformRequest: angular.identity,
                        headers: {'Content-Type': undefined}
                    }
                ).then(function() {
                    defer.resolve();
                });
            });
            
            return defer.promise;
        };

        this.readSettings = function() {
            self.settings.url = '';
            self.settings.gallery = {id: 1};
            if (!fs.existsSync(settingsfile)) {
                return;
            }
            var data = fs.readFileSync(settingsfile);
            var settings = JSON.parse(data);
            angular.forEach(settings, function(value, key) {
                self.settings[key] = value;
            });
        };

        this.writeSettings = function() {
            fs.writeFile(settingsfile, JSON.stringify(self.settings));
        };

        this.csrf = function() {
            var defer = $q.defer();
            self.csrfPromise = defer.promise;

            if (!self.settings.url) {
                defer.reject();
                return;
            }
            $http.get(self.settings.url + '/frog/csrf').then(function(res) {
                console.log(res);
                $http.defaults.headers.common['X-CSRFToken'] = res.data.value;
            }).then(function() {
                defer.resolve();
            });            
        };

        this.login = function(email, password) {
            var defer = $q.defer();
            this.csrf();
            self.csrfPromise.then(function() {
                $http.post(
                    self.settings.url + '/frog/login',
                    {'body': {'email': email, 'password': password}},
                    {
                        withCredentials: true,
                    }
                ).then(function(result) {
                    console.log(document.cookie);
                    defer.resolve(result);
                });
            });

            return defer.promise;
        };

        this.getGalleries = function() {
            return $http.get(self.settings.url + '/frog/gallery');
        }
    }

    return new factory();
});
