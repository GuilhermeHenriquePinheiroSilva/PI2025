import { Component, ExperimentalPendingTasks, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AppComponent } from '../../../app.component';

@Component({
  selector: 'app-gift-card-template',
  standalone: true,
  imports: [
    RouterLink
  ],
  templateUrl: './gift-card-template.component.html',
  styleUrl: './gift-card-template.component.css'
})
export class GiftCardTemplateComponent extends AppComponent{
  @Input() gcName: string = '';
  @Input() gcText: string | null = null;
  @Input() gcImg: string = '';
  @Input() gcImgAlt: string = '';
  @Input() gcDesc: string = '';
} 
