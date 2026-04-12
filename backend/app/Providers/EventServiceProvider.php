<?php

namespace App\Providers;

use Illuminate\Foundation\Support\Providers\EventServiceProvider as ServiceProvider;

/*
    use this when using Event::listen, otherwise EventServiceProvider with $listen property

*/

use Illuminate\Support\Facades\Event;
// use Illuminate\Support\ServiceProvider; 


class EventServiceProvider extends ServiceProvider
{
    /**
     * Register services.
     */

    protected $listen = [
        \App\Events\VideoProgressUpdated::class => [
            \App\Listeners\VideoProgressListerner::class,
        ],
    ];
}
