<?php

use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('welcome');
});

Route::get('/video', fn () => '<h2>StreamForge is running yeah</h2>');
