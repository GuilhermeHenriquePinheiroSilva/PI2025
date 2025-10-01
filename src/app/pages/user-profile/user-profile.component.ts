import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';
import { FooterComponent } from '../shared/footer/footer.component';
import { MyPurchasesComponent } from '../my-purchases/my-purchases.component';
import { FormsModule } from '@angular/forms';
import { GcGuideComponent } from '../gc-guide/gc-guide.component';

@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [
    CommonModule, NavBarComponent, FooterComponent, MyPurchasesComponent, FormsModule, GcGuideComponent
  ],
  templateUrl: './user-profile.component.html',
  styleUrl: './user-profile.component.css'
})
export class UserProfileComponent extends NavBarComponent {
    options : String = 'Mp'
}
