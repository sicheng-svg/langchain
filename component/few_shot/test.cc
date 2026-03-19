#include<iostream>
#include<vector>
#include<algorithm>

int get_close_num(std::vector<int> nums, int target) {
    std::sort(nums.begin(), nums.end());
    int left = 0, right = nums.size() - 1;
    int ans = nums[left] + nums[right];
    while (left < right) {
        int sum = nums[left] + nums[right];
        if (std::abs(sum - target) < std::abs(ans - target))
            ans = sum;
        if (sum < target) left++;
        else if (sum > target) right--;
        else return target;
    }
    return ans;
}

int main(){
    std::cout << get_close_num({1, 2, 4, 8, 13}, 15);
    return 0;
}