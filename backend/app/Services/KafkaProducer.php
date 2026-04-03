<?php

namespace App\Services;

use longlang\phpkafka\Producer\Producer;
use longlang\phpkafka\Producer\ProducerConfig;

class KafkaProducer
{
    private Producer $producer;

    public function __construct()
    {
        $config = new ProducerConfig();
        $config->setBootstrapServer(env("KAFKA_BROKERS", "localhost:9092"));
        $this->producer = new Producer($config);
    }

    public function publish(string $topic, array $payload): void
    {
        $this->producer->send($topic, json_encode($payload));
    }
}