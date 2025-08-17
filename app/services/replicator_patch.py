"""
Patch for Enhanced Replicator Service
======================================
"""

def get_dashboard_stats_fixed(self):
    """Get dashboard statistics - FIXED VERSION"""
    uptime = (datetime.now() - self.stats['start_time']).total_seconds()
    
    # Return dict directly without await
    return {
        "messages_received": self.stats.get('messages_received', 0),
        "messages_replicated": self.stats.get('messages_replicated', 0),
        "messages_filtered": self.stats.get('messages_filtered', 0),
        "images_processed": self.stats.get('images_processed', 0),
        "videos_processed": self.stats.get('videos_processed', 0),
        "watermarks_applied": self.stats.get('watermarks_applied', 0),
        "errors": self.stats.get('errors', 0),
        "uptime_seconds": uptime,
        "uptime_hours": uptime / 3600,
        "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
        "groups_configured": len(self.stats.get('groups_active', [])),
        "groups_active": len(self.stats.get('groups_active', [])),
        "is_running": self.is_running,
        "is_listening": self.is_listening,
        "last_message": (
            self.stats['last_message_time'].isoformat() 
            if self.stats.get('last_message_time') else None
        ),
        "success_rate": (
            (self.stats.get('messages_replicated', 0) / 
             max(self.stats.get('messages_received', 1), 1)) * 100
        )
    }
