
import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Notification, NotificationService } from '../../../../services/notification.service'; 
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-notification-popup',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './notification-popup.component.html',
  styleUrl: './notification-popup.component.css'
})
export class NotificationPopupComponent implements OnInit, OnDestroy {
  notifications: Notification[] = [];
  private notificationSubscription!: Subscription;

  constructor(private notificationService: NotificationService) {}

  ngOnInit(): void {
    this.notificationSubscription = this.notificationService.notifications$.subscribe(notification => {
      if (notification.type === 'remove') {
        this.notifications = this.notifications.filter(n => n.id !== notification.id);
      } else {
        this.notifications.push(notification);
      }
    });
  }

  ngOnDestroy(): void {
    if (this.notificationSubscription) {
      this.notificationSubscription.unsubscribe();
    }
  }

  getNotificationClass(type: string): string {
    if (type === 'remove') {
      return '';
    }
    return `notification-${type}`;
  }
}