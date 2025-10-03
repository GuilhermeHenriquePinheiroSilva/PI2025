import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ValidateEnterprisesComponent } from './validate-enterprises.component';

describe('ValidateEnterprisesComponent', () => {
  let component: ValidateEnterprisesComponent;
  let fixture: ComponentFixture<ValidateEnterprisesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ValidateEnterprisesComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ValidateEnterprisesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
