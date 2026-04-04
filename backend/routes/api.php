<?php

use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\VideoController;
use Illuminate\Support\Facades\Route;

Route::post("/register", [AuthController::class, "register"]);
Route::post("/login", [AuthController::class, "login"]);

Route::middleware("auth:sanctum")->group(function () {
    Route::post("/logout", [AuthController::class, "logout"]);

    Route::prefix("videos")->group(function () {
        Route::get("/", [VideoController::class, "list"]);

        Route::post("/upload", [VideoController::class, "createUpload"]);
        Route::post("/{id}/uploaded", [VideoController::class, "markUploaded"]);

        Route::get("/{id}/show", [VideoController::class, "show"]);
        Route::get("/tempurl/{video}", [VideoController::class, "getTempUrl"]);
    });
});

Route::post("videos/internal/progress/{id}", [VideoController::class, "updateVideoProgress"]);