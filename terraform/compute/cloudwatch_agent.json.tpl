{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "metrics": {
    "namespace": "Exam2/Sales",
    "metrics_collected": {
      "mem": {
        "measurement": ["mem_used_percent"],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": ["used_percent"],
        "metrics_collection_interval": 60,
        "resources": ["/"],
        "ignore_file_system_types": ["tmpfs", "devtmpfs"]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/lib/docker/containers/*/*-json.log",
            "log_group_name": "${log_group_name}",
            "log_stream_name": "{instance_id}/docker",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
