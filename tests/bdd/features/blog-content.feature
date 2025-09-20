# BDD Scenarios: Blog Content Management
# Linked to: US-001, US-002 (Blog Content Epic)

@blog_content @functional @mvp
Feature: Blog Content Display
  As a blog visitor
  I want to read blog posts on the website
  So that I can access valuable content without barriers

  Background:
    Given the blog application is running
    And the database contains sample blog posts
    And GDPR compliance is enabled

  @smoke @priority_high
  Scenario: View blog homepage with posts
    Given I am a blog visitor
    When I navigate to the blog homepage
    Then I should see a list of published blog posts
    And each post should display title, excerpt, and publication date
    And the page should load within 2 seconds

  @functional @seo
  Scenario: View individual blog post
    Given I am on the blog homepage
    And there is a published post titled "Sample Blog Post"
    When I click on the post title "Sample Blog Post"
    Then I should be redirected to the full blog post page
    And I should see the complete post content
    And the post should have proper SEO meta tags
    And the page should be accessible (WCAG 2.1 AA)

  @functional @navigation
  Scenario: Navigate between blog posts
    Given I am reading a blog post
    And there are other published posts available
    When I look for navigation options
    Then I should see "Previous Post" and "Next Post" links
    And clicking these links should take me to adjacent posts

  @functional @search
  Scenario: Search for blog content
    Given I am on the blog homepage
    And there are posts containing the word "GDPR"
    When I search for "GDPR"
    Then I should see search results containing posts with "GDPR"
    And the results should be ranked by relevance

  @functional @categories
  Scenario: Filter posts by category
    Given I am on the blog homepage
    And there are posts in "Technology" and "Privacy" categories
    When I filter by "Technology" category
    Then I should only see posts from the "Technology" category
    And the filter should be clearly indicated in the UI

  @performance @non_functional
  Scenario: Blog performance requirements
    Given I am a blog visitor
    When I access any blog page
    Then the page should load within 2 seconds
    And images should be optimized and lazy-loaded
    And the Core Web Vitals should meet Google standards

  @gdpr @privacy @no_tracking
  Scenario: Reading blog without tracking
    Given I am a new visitor who hasn't given consent
    When I read blog posts
    Then no personal data should be collected
    And no tracking cookies should be set
    And no analytics data should be gathered
    And I should still have full access to content