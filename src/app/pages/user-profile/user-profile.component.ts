import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NavBarComponent } from '../shared/nav-bar/nav-bar.component';
import { FooterComponent } from '../shared/footer/footer.component';
import { MyPurchasesComponent } from '../my-purchases/my-purchases.component';
import { FormsModule } from '@angular/forms';
import { GcGuideComponent } from '../gc-guide/gc-guide.component';
import { RouterModule } from '@angular/router';
import { Enterprise } from '../../models/enterprise.model';
import { EnterpriseService } from '../../../services/enterprise.service';
import { AuthService } from '../../../services/auth.service';
import { User } from '../../models/user.model';

@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [
    CommonModule, NavBarComponent, FooterComponent, MyPurchasesComponent, FormsModule, GcGuideComponent, RouterModule
  ],
  templateUrl: './user-profile.component.html',
  styleUrl: './user-profile.component.css'
})
export class UserProfileComponent implements OnInit {
    options : String = 'Mp';
    enterpriseDetails: Enterprise | null = null;
    isLoadingEnterprise = true;
    user: User | null = null;

    constructor(
      private enterpriseService: EnterpriseService,
      private authService: AuthService,
    ) {}

    ngOnInit(): void {
      this.authService.user$.subscribe(user => {
        this.user = user;
      });
      this.loadEnterpriseDetails();
    }

    loadEnterpriseDetails(): void {
      this.isLoadingEnterprise = true;
      this.enterpriseService.getMyEnterprise().subscribe({
        next: (data) => {
          this.enterpriseDetails = data;
          this.isLoadingEnterprise = false;
        },
        error: (err) => {
          this.enterpriseDetails = null; // Nenhuma empresa encontrada
          this.isLoadingEnterprise = false;
        }
      });
    }
}