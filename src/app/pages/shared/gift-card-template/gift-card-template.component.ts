import { Component, ExperimentalPendingTasks, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AppComponent } from '../../../app.component';
import { GiftCard } from '../../../../services/giftcard.service';
import { CommonModule } from '@angular/common';


@Component({
  selector: 'app-gift-card-template',
  standalone: true,
  imports: [
    RouterLink,
    CommonModule
  ],
  templateUrl: './gift-card-template.component.html',
  styleUrl: './gift-card-template.component.css'
})
export class GiftCardTemplateComponent extends AppComponent{
  @Input() giftCard!: GiftCard;
  @Input() gcName: string = '';
  @Input() gcText: string | null = null;
  @Input() gcImg: string = '';
  @Input() gcImgAlt: string = '';
  @Input() gcDesc: string = '';
  @Input() bgColor: string = '';
} 
