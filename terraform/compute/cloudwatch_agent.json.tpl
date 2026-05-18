{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root",
    "append_dimensions": {
      "InstanceId": "$${aws:InstanceId}"
    }
  },
  "metrics": {
    "namespace": "Exam2/Sales",
    "append_dimensions": {
      "InstanceId": "$${aws:InstanceId}"
    },
    "aggregation_dimensions": [["InstanceId"]],
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
