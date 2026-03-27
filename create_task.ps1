$action = New-ScheduledTaskAction -Execute "D:\scripts\clash-sub\update_sub.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 8am
Register-ScheduledTask -TaskName "ClashSubUpdate" -Action $action -Trigger $trigger -Force
