# Pester

Describe "Get-WindowsImageState" {
    BeforeAll {
        New-Item -Path TestRegistry:\ -Name State
        $Check = "Windows sysprep image state complete"
    }
  
    Context "Calling Get-WindowsImageState" {
        It 'When ImageState = IMAGE_STATE_COMPLETE' {
            $ImageState = "IMAGE_STATE_COMPLETE"
            New-ItemProperty -Path "TestRegistry:\State" -Name "ImageState" -Value $ImageState

            $output = Get-WindowsImageState -Key TestRegistry:\State
                
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Pass"
            $output.Note | Should -Be "Image state is $ImageState. This is the desired state"
        }

        It 'When ImageState != IMAGE_STATE_COMPLETE' {
            $ImageState = "IMAGE_STATE_UNDEPLOYABLE"
            Set-ItemProperty -Path "TestRegistry:\State" -Name "ImageState" -Value $ImageState

            $output = Get-WindowsImageState -Key TestRegistry:\State
            
            $output.Check | Should -Be $Check
            $output.Value | Should -Be "Fail"
            $output.Note | Should -Be "The state of windows Image is $ImageState"
        }        
    } 
    AfterAll {
        Remove-ItemProperty -Path "TestRegistry:\State" -Name "ImageState"
        Remove-Item -Path TestRegistry:\State
    }
}